from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Organization, Model, Tag, User
from app.schemas import CategoryTree, OrganizationResponse, ModelResponse, TagResponse
from app.api.endpoints.auth import get_current_user

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("/", response_model=CategoryTree)
async def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取分类树（用于侧边栏）
    """
    # 获取套图（按专辑数量从大到小排序）
    orgs = db.query(Organization).order_by(Organization.album_count.desc()).all()
    org_list = [
        OrganizationResponse(
            id=org.id,
            name=org.name,
            description=org.description,
            album_count=org.album_count,
            cover_url=org.cover_url,
            created_at=org.created_at
        ) for org in orgs
    ]
    
    # 获取模特（按专辑数量从大到小排序）
    models = db.query(Model).order_by(Model.album_count.desc()).all()
    model_list = [
        ModelResponse(
            id=model.id,
            name=model.name,
            description=model.description,
            album_count=model.album_count,
            cover_url=model.cover_url,
            created_at=model.created_at
        ) for model in models
    ]
    
    # 获取通用标签（按专辑数量从大到小排序）
    tags = db.query(Tag).filter(Tag.type == 'tag').order_by(Tag.album_count.desc()).all()
    tag_list = [
        TagResponse(
            id=tag.id,
            name=tag.name,
            type=tag.type,
            description=tag.description,
            album_count=tag.album_count,
            created_at=tag.created_at
        ) for tag in tags
    ]
    
    return CategoryTree(
        org=org_list,
        model=model_list,
        tag=tag_list
    )

@router.get("/org", response_model=List[OrganizationResponse])
async def get_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有套图（按专辑数量从大到小排序）"""
    orgs = db.query(Organization).order_by(Organization.album_count.desc()).all()
    return [
        OrganizationResponse(
            id=org.id,
            name=org.name,
            description=org.description,
            album_count=org.album_count,
            cover_url=org.cover_url,
            created_at=org.created_at
        ) for org in orgs
    ]

@router.get("/model", response_model=List[ModelResponse])
async def get_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有模特（按专辑数量从大到小排序）"""
    models = db.query(Model).order_by(Model.album_count.desc()).all()
    return [
        ModelResponse(
            id=model.id,
            name=model.name,
            description=model.description,
            album_count=model.album_count,
            cover_url=model.cover_url,
            created_at=model.created_at
        ) for model in models
    ]

@router.get("/tag", response_model=List[TagResponse])
async def get_tags(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有标签（按专辑数量从大到小排序）"""
    tags = db.query(Tag).filter(Tag.type == 'tag').order_by(Tag.album_count.desc()).all()
    return [
        TagResponse(
            id=tag.id,
            name=tag.name,
            type=tag.type,
            description=tag.description,
            album_count=tag.album_count,
            created_at=tag.created_at
        ) for tag in tags
    ]