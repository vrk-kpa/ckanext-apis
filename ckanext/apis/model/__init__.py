import logging

from ckan.model.domain_object import DomainObject
from ckan.model.meta import Session, metadata
from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.ext.declarative import declarative_base

from ckan import model

log = logging.getLogger(__name__)

Base = declarative_base(metadata=metadata)


class ApisetPackageAssociation(DomainObject, Base):
    __tablename__: str = 'apiset_package_association'
    package_id = Column(
        types.UnicodeText,
        ForeignKey("package.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    apiset_id = Column(
        types.UnicodeText,
        ForeignKey("package.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    @classmethod
    def get_package_ids_for_apiset(cls, apiset_id):
        apiset_package_association_list = Session.query(cls.package_id).filter_by(apiset_id=apiset_id).all()
        return apiset_package_association_list

    @classmethod
    def get_apiset_ids_for_package(cls, package_id):
        package_apiset_association_list = Session.query(cls.apiset_id).filter_by(package_id=package_id).all()
        return package_apiset_association_list

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
