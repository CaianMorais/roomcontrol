from sqlalchemy import or_
from app.models.collaborator import Collaborator

def filter_collaborators(query, search, status):
    if search:
        query = query.filter(
            or_(Collaborator.cpf.ilike(f"%{search}%"),
                Collaborator.firstname.ilike(f"%{search}%"),
                Collaborator.lastname.ilike(f"%{search}%")
            )
        )

    if status == "active":
        query = query.filter(Collaborator.is_active == True)


    elif status == "inactive":
        query = query.filter(Collaborator.is_active == False)

    return query
