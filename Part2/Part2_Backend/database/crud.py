from .models import User, Group, File

def create_group(session, user_id, title, description, is_domain_specific, genomes, num_genes, num_domains):
    group = Group(
        user_id=user_id,
        title=title,
        description=description,
        is_domain_specific=is_domain_specific,
        genomes=genomes,
        num_genes=int(num_genes),
        num_domains=int(num_domains)
    )
    session.add(group)
    session.flush() 
    return group

def create_user(session, user_id, email):
    user = User(id=user_id, email=email)
    session.add(user)
    session.flush()
    return user

def add_file(session, group_id, user_id, file_name, s3_key, file_format):
    file = File(
        group_id=group_id,
        user_id=user_id,
        file_name=file_name,
        s3_key=s3_key,
        file_type=file_format
    )
    session.add(file)

def get_first_or_none(session, model, **filters):
    return session.query(model).filter_by(**filters).first()

def get_all(session, model, **filters):
    return session.query(model).filter_by(**filters).all()

def delete(session, model_obj):
    session.delete(model_obj)


