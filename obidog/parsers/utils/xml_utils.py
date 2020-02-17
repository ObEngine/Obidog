def get_content(node):
    return ''.join(node.itertext())

def get_content_if(node):
    if node != None:
        return ''.join(node.itertext())
    else:
        return None

def extract_xml_value(tree, path):
    if len(tree.xpath(path)) > 0:
        return get_content(tree.xpath(path)[0])
    else:
        return None
