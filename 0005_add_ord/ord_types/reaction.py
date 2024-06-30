from dataclasses import dataclass


@dataclass
class ReactionComponent:
    state: str
    inchi: str
    amount: str
    reaction_role: str
    reaction_id: str

    def __iter__(self):
        yield "state", self.state
        yield "inchi", self.inchi
        yield "amount", self.amount
        yield "reaction_role", self.reaction_role
        yield "reaction_id", self.reaction_id
