def find_obidog_flag(tree, flag_name, amount=None):
    search_for = f"obidog.{flag_name}:"
    flags = [
        elem.attrib["url"][len(search_for)::]
        for elem in
        tree.xpath(f".//ulink[starts-with(@url, '{search_for}')]")
    ]
    if amount:
        if len(flags) > amount:
            raise RuntimeError(
                f"Obidog flag {flag_name} found "
                f"{len(flags)} times but is needed {amount} times"
            )
    return flags

def parse_obidog_flags(tree):
    obidog_flags = {}
    bind_to = find_obidog_flag(tree, "bind", 1)
    if bind_to:
        obidog_flags["bind_to"] = bind_to[0]
    helpers = find_obidog_flag(tree, "helper")
    if helpers:
        obidog_flags["helpers"] = helpers
    private = find_obidog_flag(tree, "private", 1)
    if private and private[0] == "true":
        obidog_flags["private"] = True
    return obidog_flags

class ConflictsManager:
    def __init__(self):
        self.conflicts = {}
    def append(self, conflict, xml):
        if not conflict in self.conflicts:
            self.conflicts[conflict] = []
        else:
            print("Conflict detected")
        self.conflicts[conflict].append(xml)

CONFLICTS = ConflictsManager()