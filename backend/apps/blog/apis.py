import datetime
from typing import List

from core.globals import site
from fastapi import APIRouter
from fastapi_amis_admin.globals.deps import AsyncSess
from sqlalchemy import insert, select

from apps.blog.models import Article, ArticleStatus

router = APIRouter(prefix="/articles", tags=["ArticleAPI"])


# 方式一: 通过FastAPI依赖自动处理,获取session.(推荐) 特点:
# 1.同一个请求FastAPI会缓存依赖,对于多级依赖,同一个请求多次使用session对象,会减少session的获取成本.
# 2.如果`site.db`使用的是`AsyncDatabase`异步连接,则获取的是`AsyncSession`.
# 3.如果`site.db`使用的是`Database`同步连接,则获取的是`Session`.
#   2.1.同步Session可以充分利用`sqlalchemy`模型懒加载的特性.
#   2.2.注意不要在异步方法中使用同步Session,否则可能堵塞异步循环.
@router.get("/read/{id}", response_model=Article, summary="读取文章")
async def read_article(id: int, session: AsyncSess):
    return await session.get(Article, id)


@router.get("/update/{id}", response_model=Article, summary="更新文章")
async def update_article(id: int, session: AsyncSess):
    article = await session.get(Article, id)
    if article:
        article.create_time = datetime.datetime.now()
        await session.flush()
    return article


# 方式二: 通过`sqlalchemy-database`提供的快捷函数.特点:
# 1.会自动获取当前上下文的session.(请理解session的获取原理,否则不要使用此方式)
#   1.1.如果需要多次使用同一个session,可以通过封装一个函数, 使用`run_sync`方法,减少session获取成本.
# 2.通过`async_`前缀方法,可以不用区分数据库连接是同步连接,还是异步连接.
#   2.1对于特定的项目,在能确定数据库连接是同步或异步的情况下,建议明确调用对应的方法.
#   2.2如果开发一个python包,供其他人使用不能确定连接是同步或异步,应该统一使用`async_`前缀方法.


@router.get("/read2/{id}", response_model=Article, summary="读取文章")
async def read_article2(id: int):
    article = await site.db.async_get(Article, id)
    return article


@router.put("/update2/{id}", response_model=Article, summary="更新文章")
async def update_article2(id: int):
    article = await site.db.async_get(Article, id)
    if article:
        article.create_time = datetime.datetime.now()
        await site.db.async_flush()
    return article


@router.post("/create2/", response_model=int, summary="新增文章")
async def create_article2(data: Article):
    # 新增数据模型根据实际情况自己定义
    stmt = insert(Article).values(data.dict(exclude={"id"}))
    result = await site.db.async_execute(stmt)
    return result.lastrowid


@router.get("/list2", response_model=List[Article], summary="读取文章列表")
async def list_article2():
    # 通用的查询表达式可以写在ORM模型,提供一个方法调用.
    stmt = select(Article).where(Article.status == ArticleStatus.published.value).limit(10).order_by(Article.create_time)
    result = await site.db.async_scalars(stmt)
    return result.all()


# 方式三: 通过注册中间件,在每次请求时自动获取session,并在请求结束时自动关闭session.
# 注意: 必须在fastapi应用中注册中间件,才能在请求中获取session.(请理解session的获取原理,否则不要使用此方式)
# 1.如果`site.db`使用的是`AsyncDatabase`异步连接,则获取的是`AsyncSession`.
# 2.如果`site.db`使用的是`Database`同步连接,则获取的是`Session`.
# 建议在`core.globals.py`中建立一个`db`对象,用于管理数据库连接.
@router.get("/read3/{id}", response_model=Article, summary="读取文章")
async def read_article3(id: int):
    article = await site.db.session.get(Article, id)
    return article


@router.put("/update3/{id}", response_model=Article, summary="更新文章")
async def update_article3(id: int):
    article = await site.db.session.get(Article, id)
    if article:
        article.create_time = datetime.datetime.now()
        await site.db.session.flush()
    return article


@router.post("/create3/", response_model=int, summary="新增文章")
async def create_article3(data: Article):
    # 新增数据模型根据实际情况自己定义
    stmt = insert(Article).values(data.dict(exclude={"id"}))
    result = await site.db.session.execute(stmt)
    return result.lastrowid


@router.get("/list3", response_model=List[Article], summary="读取文章列表")
async def list_article3():
    # 通用的查询表达式可以写在ORM模型,提供一个方法调用.
    stmt = select(Article).where(Article.status == ArticleStatus.published.value).limit(10).order_by(Article.create_time)
    result = await site.db.session.scalars(stmt)
    return result.all()
