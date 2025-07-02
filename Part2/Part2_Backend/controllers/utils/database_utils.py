# def add_file_to_database(group_id, user_id, file_name, s3_key, file_format):
#     session.add(File(group_id=group_id, user_id=user_id, file_name=file_name, s3_key=s3_key, file_type=file_format))
#     session.commit()

# def create_group_in_database(user_id, title, description, is_domain_specific, genomes, num_genes, num_domains):
#     new_group = Group(
#         user_id=user_id,
#         title=title,
#         description=description,
#         is_domain_specific=is_domain_specific,
#         genomes=genomes,
#         num_genes=int(num_genes),
#         num_domains=int(num_domains)
#     )
#     session.add(new_group)
#     session.commit()