class Sequence:
    def __init__(self, actif: bool, name: str, time: int, weight_goal: int=0, next_sequence=None):
        self.actif = actif
        self.name = name
        self.time = time
        self.weight_goal = weight_goal
        self.next = next_sequence

    @classmethod
    def from_list(cls, sequence_list):
        if not sequence_list:
            return None

        head = cls(*sequence_list[0])
        current = head
        for item in sequence_list[1:]:
            next_sequence = cls(*item)
            current.next = next_sequence
            current = next_sequence

        return head

    @staticmethod
    def from_file(filename):
        """

        """
        file = open(filename, mode='r')
        input_string = file.read().split('\n') 
        #print(input_string)
        
        sequence_list = []
        
        for line in input_string :
            parts = line.split(" | ")
            print(parts)
            for _ in range(int(parts[0])):
                tmp1 = parts[1].split("\"")
                tmp1_1 = tmp1[2].split(" ")
                sequence_list.append((int(tmp1[0]), tmp1[1], int(tmp1_1[0]), int(tmp1_1[1])))
                tmp2 = parts[2].split("\"")
                sequence_list.append((int(tmp2[0]), tmp2[1], int(tmp2[2])))
        return Sequence.from_list(sequence_list)

    def __str__(self):
        """
        Retourne une représentation en chaîne de caractères de la séquence.
        """
        return f"Sequence(name='{self.name}', actif={self.actif}, time={self.time}, weight_goal={self.weight_goal})"

# Exemple d'utilisation
if __name__ == "__main__":
    first_sequence = Sequence.from_file("emil.sq")

    current = first_sequence
    while current:
        print(current)
        current = current.next
