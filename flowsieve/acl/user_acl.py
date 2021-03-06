from flowsieve.acl.acl_result import ACLResult, PacketMatch
from flowsieve.acl.base_acl import BaseACL
from flowsieve.acl.user_set import UserSet

from ryu.lib.packet import ethernet


class UserACL(BaseACL):
    def __init__(self, **kwargs):
        super(UserACL, self).__init__(**kwargs)
        self.allowed_user_names = kwargs.get("allowed_users", [])
        self.allowed_users = []
        self.allowed_role_names = kwargs.get("allowed_roles", [])
        self.allowed_roles = []
        self.denied_user_names = kwargs.get("denied_users", [])
        self.denied_users = []
        self.denied_role_names = kwargs.get("denied_roles", [])
        self.denied_roles = []
        self.is_family = kwargs.get("family", True)
        self.default = kwargs.get("default", "")

        self.user_set = UserSet.empty()

    def set_default(self):
        if self.default != "":
            return
        elif self.parent is None:
            self.default = "allow"
        else:
            self.default = "inherit"

    def load_relations(self, user_store):
        self.set_default()

        for user_name in self.allowed_user_names:
            user = user_store.get_user(user_name)
            if user is None:
                self._logger.warning("Unknwon user %s in section"
                                     " allowed_users of an ACL", user_name)
                continue
            self.allowed_users.append(user)

        for role_name in self.allowed_role_names:
            role = user_store.get_role(role_name)
            if role is None:
                self._logger.warning("Unknown role %s in section"
                                     " allowed_roles of an ACL", role_name)
                continue
            self.allowed_roles.append(role)

        for user_name in self.denied_user_names:
            user = user_store.get_user(user_name)
            if user is None:
                self._logger.warning("Unknwon user %s in section"
                                     " denied_users of an ACL", user_name)
                continue
            self.denied_users.append(user)

        for role_name in self.denied_role_names:
            role = user_store.get_role(role_name)
            if role is None:
                self._logger.warning("Unknown role %s in section"
                                     " denied_roles of an ACL", role_name)
                continue
            self.denied_roles.append(role)

        self.build_user_set()

    def build_user_set(self):
        self.user_set = UserSet.whole()

        default_str_low = self.default.lower()
        if default_str_low == "deny":
            self.user_set = UserSet.empty()
        elif default_str_low == "allow":
            self.user_set = UserSet.whole()
        elif default_str_low == "inherit" and self.parent is not None:
            self.parent.build_user_set()
            self.user_set = self.parent.user_set
        else:
            self._logger.warning("Unknown default value %s", self.default)

        if self.user is None and self.role is not None:
            my_family = UserSet(roles=[self.role])
            if self.is_family:
                self.user_set += my_family
            else:
                self.user_set -= my_family

        if self.user is not None:
            self.user_set += UserSet(users=[self.user])

        self.user_set += UserSet(users=self.allowed_users)
        self.user_set += UserSet(roles=self.allowed_roles)
        self.user_set -= UserSet(users=self.denied_users)
        self.user_set -= UserSet(roles=self.denied_roles)

    def allows_packet(self, pkt, src_user):
        if pkt is None:
            return ACLResult(src_user in self.user_set, PacketMatch())

        eth = pkt.get_protocol(ethernet.ethernet)
        return ACLResult(src_user in self.user_set,
                         PacketMatch(dl_dst=eth.dst))

    def __repr__(self):
        repr_family = ""
        if self.is_family:
            repr_family = " family"

        return "<UserACL{0} allowed_users={1}>".format(
            repr_family, self.allowed_user_names
        )
