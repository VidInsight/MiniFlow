def module():
    return AdditionModule()

class AdditionModule:
    def run(self, context):
        # Get parameters from context
        num1 = context.get("num1", 0)
        num2 = context.get("num2", 0)
        
        # Perform addition
        result = num1 + num2
        
        # Return result in expected format
        return {
            "sum": result,
            "operation": f"{num1} + {num2} = {result}"
        }