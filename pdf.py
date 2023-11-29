import evadb
cursor = evadb.connect(evadb_dir="./eva_db").cursor()

query = """ LOAD PDF '/home/oscar/cv2.pdf' INTO pdfs; """

print(cursor.query(query).df())