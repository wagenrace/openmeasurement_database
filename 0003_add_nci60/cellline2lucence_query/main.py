import re


def cellline2lucence_query(cellline):
    clean_cellline = cellline.split("/")[0].lower()
    elements = re.findall("[a-z]+|\d+", clean_cellline)

    full_name = "".join(elements)
    all_options = " AND ".join(elements)
    simple_options = clean_cellline.replace("-", " AND ")
    query = f"{full_name} OR ({all_options}) OR ({simple_options})"

    return query
