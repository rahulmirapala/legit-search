#!/usr/bin/env python3
"""Add sample legal documents for testing."""
import sys
sys.path.insert(0, '/home/chakri/Documents/Projects/legit-search')

from elasticsearch import Elasticsearch
from app.config import get_settings

settings = get_settings()
es = Elasticsearch(settings.es_host)

# Sample Indian Supreme Court cases
sample_docs = [
    {
        "case_name": "Kesavananda Bharati v. State of Kerala",
        "citation_id": "AIR 1973 SC 1461",
        "judgment_date": "1973-04-24",
        "year": 1973,
        "court": "Supreme Court of India",
        "full_text": """Kesavananda Bharati case established the basic structure doctrine. 
        The Supreme Court held that while Parliament has wide powers to amend the Constitution, 
        it cannot alter the basic structure or framework of the Constitution. This landmark judgment 
        dealt with fundamental rights, emergency provisions, and limitations on constitutional amendments. 
        The doctrine of basic structure includes supremacy of constitution, rule of law, independence of judiciary, 
        doctrine of separation of powers, federalism, secularism, and the sovereign democratic republican structure."""
    },
    {
        "case_name": "Maneka Gandhi v. Union of India",
        "citation_id": "AIR 1978 SC 597",
        "judgment_date": "1978-01-25",
        "year": 1978,
        "court": "Supreme Court of India",
        "full_text": """Maneka Gandhi case expanded the scope of Article 21 (Right to Life and Personal Liberty). 
        The Court held that the procedure established by law must be just, fair and reasonable, not arbitrary. 
        This judgment linked Articles 14, 19 and 21 together. The case dealt with passport impounding and 
        established that personal liberty includes right to travel abroad. The golden triangle of fundamental 
        rights was recognized, emphasizing that law must satisfy both procedural and substantive requirements."""
    },
    {
        "case_name": "Vishaka v. State of Rajasthan",
        "citation_id": "AIR 1997 SC 3011",
        "judgment_date": "1997-08-13",
        "year": 1997,
        "court": "Supreme Court of India",
        "full_text": """Vishaka guidelines on sexual harassment at workplace were laid down by the Supreme Court. 
        The Court held that sexual harassment violates fundamental rights under Articles 14, 15, 19 and 21. 
        Until specific legislation was enacted, the Court prescribed guidelines to prevent sexual harassment. 
        These guidelines included defining sexual harassment, preventive measures, complaint mechanisms, 
        and disciplinary action. This was a landmark case in protecting women's rights and dignity at workplace. 
        The guidelines remained in force until the Sexual Harassment of Women at Workplace Act, 2013."""
    },
    {
        "case_name": "Indra Sawhney v. Union of India",
        "citation_id": "AIR 1993 SC 477",
        "judgment_date": "1992-11-16",
        "year": 1992,
        "court": "Supreme Court of India",
        "full_text": """Indra Sawhney case (Mandal Commission case) dealt with reservations for Other Backward Classes (OBC). 
        The Supreme Court upheld 27% reservation for OBCs in central government jobs and educational institutions. 
        The Court ruled that total reservations cannot exceed 50%, except in extraordinary situations. 
        Creamy layer concept was introduced to exclude affluent members of backward classes. The judgment 
        balanced social justice with merit and efficiency. Economic criterion alone cannot determine backwardness. 
        Reservation in promotions was held impermissible, though this was later modified."""
    },
    {
        "case_name": "Minerva Mills v. Union of India",
        "citation_id": "AIR 1980 SC 1789",
        "judgment_date": "1980-07-31",
        "year": 1980,
        "court": "Supreme Court of India",
        "full_text": """Minerva Mills strengthened the basic structure doctrine established in Kesavananda Bharati. 
        The Court struck down provisions of 42nd Amendment that gave unlimited amending power to Parliament. 
        It held that the Constitution is founded on harmony between Part III (Fundamental Rights) and 
        Part IV (Directive Principles). One cannot be given absolute supremacy over the other. 
        Judicial review is a basic feature. The power to amend does not include power to destroy or abrogate 
        the basic structure. Limited government is a basic feature of Indian Constitution."""
    },
    {
        "case_name": "M.C. Mehta v. Union of India (Oleum Gas Leak)",
        "citation_id": "AIR 1987 SC 1086",
        "judgment_date": "1986-12-20",
        "year": 1986,
        "court": "Supreme Court of India",
        "full_text": """M.C. Mehta case established the principle of absolute liability for hazardous industries. 
        The Supreme Court evolved a stricter liability regime than Rylands v Fletcher for hazardous activities. 
        Enterprises engaged in inherently dangerous activities are absolutely liable for harm caused, 
        with no exceptions. The measure of compensation must correlate with magnitude and capacity of enterprise. 
        This case arose from oleum gas leak in Delhi. Public interest litigation was used to protect 
        environment and public health. Right to healthy environment is part of Article 21."""
    },
    {
        "case_name": "Navtej Singh Johar v. Union of India",
        "citation_id": "(2018) 10 SCC 1",
        "judgment_date": "2018-09-06",
        "year": 2018,
        "court": "Supreme Court of India",
        "full_text": """Navtej Singh Johar case decriminalized homosexuality by reading down Section 377 IPC. 
        The Supreme Court held that consensual sexual acts between adults in private cannot be criminalized. 
        Section 377 violated rights to equality, dignity, privacy and non-discrimination. Sexual orientation 
        is biological and natural. LGBTQ+ persons have same constitutional rights as others. The judgment 
        emphasized transformative constitutionalism and constitutional morality over social morality. 
        History owes an apology to LGBTQ+ community for ostracization and persecution."""
    },
    {
        "case_name": "Justice K.S. Puttaswamy v. Union of India",
        "citation_id": "(2017) 10 SCC 1",
        "judgment_date": "2017-08-24",
        "year": 2017,
        "court": "Supreme Court of India",
        "full_text": """K.S. Puttaswamy case recognized right to privacy as fundamental right under Article 21. 
        Nine-judge bench unanimously held that privacy is intrinsic to life and liberty. It includes 
        decisional autonomy, informational privacy and bodily integrity. Privacy is not absolute and 
        can be restricted by proportionate state action for legitimate aims. The judgment overruled 
        earlier decisions that denied privacy as fundamental right. This formed basis for subsequent 
        challenges to Aadhaar and other data collection schemes. Privacy is essential for dignity."""
    }
]

# Index the documents
for i, doc in enumerate(sample_docs):
    es.index(index=settings.index_name, id=i+1, document=doc)
    print(f"Indexed: {doc['case_name']}")

print(f"\nSuccessfully indexed {len(sample_docs)} sample documents.")
print("You can now search for terms like 'fundamental rights', 'privacy', 'harassment', 'reservation', etc.")
