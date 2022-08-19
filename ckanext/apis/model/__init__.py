from ckan.model import DomainObject
from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import types
from ckan.model.meta import metadata, mapper, Session
from ckan import model
import logging

log = logging.getLogger(__name__)
apiset_package_association_table = None
apiset_admin_table = None


def setup():
    if apiset_package_association_table is None:
        define_apiset_package_association_table()
        log.debug('ApisetPackageAssociation table defined in memory')

    if model.package_table.exists():
        if not apiset_package_association_table.exists():
            apiset_package_association_table.create()
            log.debug('ApisetPackageAssociation table create')
        else:
            log.debug('ApisetPackageAssociation table already exists')
    else:
        log.debug('ApisetPackageAssociation table creation deferred')

    if apiset_admin_table is None:
        define_apiset_admin_table()
        log.debug('ApisetAdmin table defined in memory')

    if model.user_table.exists():
        if not apiset_admin_table.exists():
            apiset_admin_table.create()
            log.debug('ApisetAdmin table create')
        else:
            log.debug('ApisetAdmin table already exists')
    else:
        log.debug('ApisetAdmin table creation deferred')


class ApisetBaseModel(DomainObject):
    @classmethod
    def filter(cls, **kwargs):
        return Session.query(cls).filter_by(**kwargs)

    @classmethod
    def exists(cls, **kwargs):
        if cls.filter(**kwargs).first():
            return True
        else:
            return False

    @classmethod
    def get(cls, **kwargs):
        instance = cls.filter(**kwargs).first()
        return instance

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        Session.add(instance)
        Session.commit()
        return instance.as_dict()


class ApisetPackageAssociation(ApisetBaseModel):
    @classmethod
    def get_package_ids_for_apiset(cls, apiset_id):
        apiset_package_association_list = Session.query(cls.package_id).filter_by(apiset_id=apiset_id).all()
        return apiset_package_association_list

    @classmethod
    def get_apiset_ids_for_package(cls, package_id):
        package_apiset_association_list = Session.query(cls.apiset_id).filter_by(package_id=package_id).all()
        return package_apiset_association_list


def define_apiset_package_association_table():
    global apiset_package_association_table

    apiset_package_association_table = Table(
        'apiset_package_association', metadata,
        Column('package_id', types.UnicodeText,
               ForeignKey('package.id',
                          ondelete='CASCADE',
                          onupdate='CASCADE'),
               primary_key=True, nullable=False),
        Column('apiset_id', types.UnicodeText,
               ForeignKey('package.id',
                          ondelete='CASCADE',
                          onupdate='CASCADE'),
               primary_key=True, nullable=False)
    )

    mapper(ApisetPackageAssociation, apiset_package_association_table)


class ApisetAdmin(ApisetBaseModel):

    @classmethod
    def get_apiset_admin_ids(cls):
        id_list = [i for (i, ) in Session.query(cls.user_id).all()]
        return id_list

    @classmethod
    def is_user_apiset_admin(cls, user):
        return (user.id in cls.get_apiset_admin_ids())


def define_apiset_admin_table():
    global apiset_admin_table

    apiset_admin_table = Table('apiset_admin', metadata,
                                 Column('user_id', types.UnicodeText,
                                        ForeignKey('user.id',
                                                   ondelete='CASCADE',
                                                   onupdate='CASCADE'),
                                        primary_key=True, nullable=False))

    mapper(ApisetAdmin, apiset_admin_table)
