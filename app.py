from flask import Flask
from flask_restful import Api
from resources.minions import MinionsKeys, MinionsStatus
from user.product import ProductList, Product
from user.user import User, Login
from resources.log import LogList

app = Flask(__name__)
api = Api(app)

# login
#api.resources(Login, "/login")

# product
api.add_resource(ProductList, "/saltshaker/api/v1.0/product")
api.add_resource(Product, "/saltshaker/api/v1.0/product/<string:product_id>")

# user
api.add_resource(User, "/saltshaker/api/v1.0/user")

# minions
api.add_resource(MinionsStatus, "/saltshaker/api/v1.0/minions/status")
api.add_resource(MinionsKeys, "/saltshaker/api/v1.0/minions/keys")


# audit log
api.add_resource(LogList, "/saltshaker/api/v1.0/log")


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
