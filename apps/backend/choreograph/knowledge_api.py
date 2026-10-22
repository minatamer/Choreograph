from uuid import UUID

from fastapi import Depends, Request, Response
from sqlalchemy import select

from . import knowledge
from .contracts import DocumentDetail, MutationView, ReplaceDocument
from .models import Chunk


def register(app):
    dependency=Depends(app.state.unit_of_work,scope='function')

    @app.get('/v1/documents/{version_id}',response_model=DocumentDetail)
    def detail(version_id:UUID,request:Request,db=dependency):
        workspace,_=app.state.authorize(request,db)
        row=knowledge.source(db,workspace,version_id)
        return {'document':next(item for item in knowledge.documents(db,workspace) if item['id']==row.id),
                'passages':[{'id':c.id,'page':c.page,'section':c.section,'content':c.content}
                            for c in db.scalars(select(Chunk).where(Chunk.version_id==row.id).order_by(Chunk.page,Chunk.id))]}

    @app.get('/v1/documents/{version_id}/source')
    def original(version_id:UUID,request:Request,db=dependency):
        workspace,_=app.state.authorize(request,db)
        row=knowledge.source(db,workspace,version_id)
        return Response(row.source,media_type=row.media_type,headers={'cache-control':'no-store',
            'content-disposition':'inline; filename="juniper-guide.pdf"' if row.media_type=='application/pdf' else 'inline; filename="juniper-guide.txt"',
            'x-content-type-options':'nosniff','content-security-policy':"sandbox; default-src 'none'"})

    @app.post('/v1/documents/{slot}/replace',response_model=MutationView)
    def replacement(slot:str,body:ReplaceDocument,request:Request):
        from .interactions import replace_document
        return replace_document(app,slot,body,request)
