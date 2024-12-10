class HistoryManager:
    def __init__(self, max_history=10):
        self.history = []
        self.redo_stack = []
        self.max_history = max_history
    
    def add(self, image):
        self.history.append(image.copy())
        self.redo_stack.clear()
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def undo(self, current_image):
        if len(self.history) > 0:
            self.redo_stack.append(current_image.copy())
            return self.history.pop()
        return current_image
    
    def redo(self, current_image):
        if len(self.redo_stack) > 0:
            self.history.append(current_image.copy())
            return self.redo_stack.pop()
        return current_image 