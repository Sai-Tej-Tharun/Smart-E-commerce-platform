import pymysql

# fastapi_backend already talks to MySQL via PyMySQL (see its
# SQLALCHEMY_DATABASE_URL). Django's ORM wants a MySQLdb-compatible driver,
# so we make PyMySQL pretend to be one rather than requiring the trickier
# `mysqlclient` C-extension install.
pymysql.install_as_MySQLdb()
