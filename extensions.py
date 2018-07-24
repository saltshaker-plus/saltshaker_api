# -*- coding:utf-8 -*-
from flask_celery import Celery
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler, BaseScheduler, BlockingScheduler
from apscheduler.executors.base import MaxInstancesReachedError
from apscheduler.util import TIMEOUT_MAX, timedelta_seconds
from datetime import datetime, timedelta
from common.db import url
from common.log import loggers
from common.redis import RedisTool
import time
from threading import Thread, Event
import six
from pytz import utc
from apscheduler.events import JobSubmissionEvent, EVENT_JOB_SUBMITTED, EVENT_JOB_MAX_INSTANCES


logger = loggers()

# 使用Flask-Celery-Helper 进行celery 的 flask 扩展
celery = Celery()


class Config(object):
    # SCHEDULER_JOBSTORES = {
    #     'default': RedisJobStore(host=redis_host, port=redis_port, db=1, password=redis_pwd, decode_responses=True)
    # }
    SCHEDULER_JOBSTORES = {
        # url="mysql+pymysql://root:123456@127.0.0.1/saltshaker_plus"
        'default': SQLAlchemyJobStore(url=url)
    }
    SCHEDULER_EXECUTORS = {
        'default': {'type': 'threadpool', 'max_workers': 20}
    }
    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': False,
        'max_instances': 5,
        'misfire_grace_time': 60
    }
    SCHEDULER_API_ENABLED = True


#: constant indicating a scheduler's stopped state
STATE_STOPPED = 0
#: constant indicating a scheduler's running state (started and processing jobs)
STATE_RUNNING = 1
#: constant indicating a scheduler's paused state (started but not processing jobs)
STATE_PAUSED = 2


# 重写BaseScheduler类的_process_jobs方法，使用redis setnx 达到互斥，确保后端存储的schedule只运行一次，
# 又能保证每个进程可以独立接收新的调度任务
class MutexBaseScheduler(BaseScheduler):
    def _process_jobs(self):
        """
        Iterates through jobs in every jobstore, starts jobs that are due and figures out how long
        to wait for the next round.

        If the ``get_due_jobs()`` call raises an exception, a new wakeup is scheduled in at least
        ``jobstore_retry_interval`` seconds.

        """
        if self.state == STATE_PAUSED:
            self._logger.debug('Scheduler is paused -- not processing jobs')
            return None

        self._logger.debug('Looking for jobs to run')
        now = datetime.now(self.timezone)
        next_wakeup_time = None
        events = []

        with self._jobstores_lock:
            for jobstore_alias, jobstore in six.iteritems(self._jobstores):
                try:
                    due_jobs = jobstore.get_due_jobs(now)
                except Exception as e:
                    # Schedule a wakeup at least in jobstore_retry_interval seconds
                    self._logger.warning('Error getting due jobs from job store %r: %s',
                                         jobstore_alias, e)
                    retry_wakeup_time = now + timedelta(seconds=self.jobstore_retry_interval)
                    if not next_wakeup_time or next_wakeup_time > retry_wakeup_time:
                        next_wakeup_time = retry_wakeup_time

                    continue

                for job in due_jobs:
                    # Look up the job's executor
                    try:
                        executor = self._lookup_executor(job.executor)
                    except BaseException:
                        self._logger.error(
                            'Executor lookup ("%s") failed for job "%s" -- removing it from the '
                            'job store', job.executor, job)
                        self.remove_job(job.id, jobstore_alias)
                        continue

                    run_times = job._get_run_times(now)
                    run_times = run_times[-1:] if run_times and job.coalesce else run_times
                    if run_times:
                        try:
                            '''互斥操作'''
                            # 获取job 的id
                            id = job.id
                            # 使用 redis setnx 进行互斥
                            status = RedisTool.setnx("%s.lock" % id, time.time())
                            # 成功存入redis key 后进行job的提交
                            if status:
                                executor.submit_job(job, run_times)
                                # 提交完成后设置redis key 过期时间为 900毫秒(周期最小1秒)
                                RedisTool.pexpire("%s.lock" % id, 900)
                            # 失败直接跳出，说明这个周期的job已经被执行过了
                            else:
                                continue
                        except MaxInstancesReachedError:
                            self._logger.warning(
                                'Execution of job "%s" skipped: maximum number of running '
                                'instances reached (%d)', job, job.max_instances)
                            event = JobSubmissionEvent(EVENT_JOB_MAX_INSTANCES, job.id,
                                                       jobstore_alias, run_times)
                            events.append(event)
                        except BaseException:
                            self._logger.exception('Error submitting job "%s" to executor "%s"',
                                                   job, job.executor)
                        else:
                            event = JobSubmissionEvent(EVENT_JOB_SUBMITTED, job.id, jobstore_alias,
                                                       run_times)
                            events.append(event)

                        # Update the job if it has a next execution time.
                        # Otherwise remove it from the job store.
                        job_next_run = job.trigger.get_next_fire_time(run_times[-1], now)
                        if job_next_run:
                            job._modify(next_run_time=job_next_run)
                            jobstore.update_job(job)
                        else:
                            self.remove_job(job.id, jobstore_alias)

                # Set a new next wakeup time if there isn't one yet or
                # the jobstore has an even earlier one
                jobstore_next_run_time = jobstore.get_next_run_time()
                if jobstore_next_run_time and (next_wakeup_time is None or
                                                       jobstore_next_run_time < next_wakeup_time):
                    next_wakeup_time = jobstore_next_run_time.astimezone(self.timezone)

        # Dispatch collected events
        for event in events:
            self._dispatch_event(event)

        # Determine the delay until this method should be called again
        if self.state == STATE_PAUSED:
            wait_seconds = None
            self._logger.debug('Scheduler is paused; waiting until resume() is called')
        elif next_wakeup_time is None:
            wait_seconds = None
            self._logger.debug('No jobs; waiting until a job is added')
        else:
            wait_seconds = min(max(timedelta_seconds(next_wakeup_time - now), 0), TIMEOUT_MAX)
            self._logger.debug('Next wakeup is due at %s (in %f seconds)', next_wakeup_time,
                               wait_seconds)

        return wait_seconds


# 重写BlockingScheduler类的_main_loop方法，使其调用MutexBaseScheduler类的_process_jobs方法
# 必须要继承MutexBaseScheduler类
class MutexBlockingScheduler(BlockingScheduler, MutexBaseScheduler):
    def _main_loop(self):
        wait_seconds = TIMEOUT_MAX
        while self.state != STATE_STOPPED:
            self._event.wait(wait_seconds)
            self._event.clear()
            wait_seconds = self._process_jobs()


# 重写BackgroundScheduler类的start方法，使其调用MutexBlockingScheduler类_main_loop方法
# 必须要继承MutexBlockingScheduler类
class MutexBackgroundScheduler(BackgroundScheduler, MutexBlockingScheduler):
    def start(self, *args, **kwargs):
        self._event = Event()
        BaseScheduler.start(self, *args, **kwargs)
        self._thread = Thread(target=self._main_loop, name='APScheduler')
        self._thread.daemon = self._daemon
        self._thread.start()


class MutexAPScheduler(APScheduler):
    # 重写APScheduler的构造方法，scheduler对象使用自定义MutexBackgroundScheduler类
    def __init__(self):
        APScheduler.__init__(self, scheduler=None, app=None)
        self._scheduler = MutexBackgroundScheduler(jobstores=Config.SCHEDULER_JOBSTORES,
                                                   executors=Config.SCHEDULER_EXECUTORS,
                                                   job_defaults=Config.SCHEDULER_JOB_DEFAULTS,
                                                   timezone=utc)


scheduler = MutexAPScheduler()


# APScheduler event 记录错误日志
def aps_listener(event):
    if event.exception:
        logger.error("The APScheduler job crashed : %s", event.exception)

