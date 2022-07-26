def encode2neo4j(string):
    # # Some synonym are between " ", remove those
    if string.startswith('"') and string.endswith('"'):
        string = string[1:-1]

    # # Neo4j wants ' as '' and " as ""
    # string = string.replace("\\", "\\\\")
    string = string.replace('\\"', '\"')
    # string = string.replace("'", "\\'")
    if "'" in string or '"' in string:
        string = f'"{string}"'

    return string
