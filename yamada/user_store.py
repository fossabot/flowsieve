import logging

from yaml import load


class UserStore(object):
    DEFAULT_USER_ROLE_FILE = "conf/user_store.yml"

    def __init__(self, file_name=None):
        super(UserStore, self).__init__()
        if file_name is None:
            file_name = UserStore.DEFAULT_USER_ROLE_FILE
        self.user_role_file = file_name
        self.users = {}
        self.roles = {}
        self._logger = logging.getLogger(self.__class__.__name__)

        self._read_definition_file()

    def get_user(self, user_name):
        return self.users.get(user_name)

    def _read_definition_file(self):
        try:
            data = load(file(self.user_role_file))
        except IOError:
            self._logger.error("Could not open %s", self.user_role_file)
            return

        if "users" in data:
            self._logger.info("Reading user data")
            self._store_user_data(data["users"])
        if "roles" in data:
            self._logger.info("Reading role data")
            self._store_role_data(data["roles"])

    def _store_user_data(self, users):
        for user in users:
            if not self._validate_user_keys(user):
                return
            name = user["name"]
            password = user["password"]
            role = user["role"]
            u = User(name, password, role)
            self.users.update({name: u})

    def _store_role_data(self, roles):
        for role in roles:
            if not self._validate_role_keys(role):
                return
            name = role["name"]
            allowed_hosts = []
            for host in role["allowed_hosts"]:
                allowed_hosts.append(host)

            r = Role(name, allowed_hosts)
            self.roles.update({name: r})

    def _validate_user_keys(self, user):
        return "name" in user and "password" in user and "role" in user

    def _validate_role_keys(self, role):
        if "name" not in role or "allowed_hosts" not in role:
            return False

        for host in role["allowed_hosts"]:
            if "name" not in host:
                return False
            if "mac" not in host and "ip" not in host:
                return False

        return True


class Role(object):
    def __init__(self, name, allowed_hosts):
        super(Role, self).__init__()
        self.name = name
        self.allowed_hosts = allowed_hosts


class User(object):
    def __init__(self, name, password, role):
        super(User, self).__init__()
        self.name = name
        self.password = password
        self.role = role