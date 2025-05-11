class Policy:
    def __init__(self, name=None, **kwargs):
        self.name = name if name is not None else "random"
        self.args = kwargs

    def __call__(self, moves, **kwargs):
        method_ref = getattr(self, self.name)
        return method_ref(moves, self.args | kwargs)
    
    def random(self, moves, args):
        import random
        return random.choice(moves)

    def immediate_value(self, moves, args):
        import random
        best_score = max([a[1] for a in moves])
        return random.choice([a for a in moves if a[1] >= best_score - args.get('policy_freedom', 0)])