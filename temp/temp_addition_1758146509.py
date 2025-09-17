import json

class AdditionNode:
    def run(self, context):
        print(f"[ADDITION NODE] Received context: {context}")
        
        # Get input value (from trigger or previous node)
        input_value = context.get('input_value')
        if input_value is None:
            previous_result = context.get('previous_result', {}).get('value')
            if previous_result is not None:
                input_value = previous_result
            else:
                input_value = 0
        
        value_to_add = context.get('value_to_add', 2)
        result = input_value + value_to_add
        
        print(f"[ADDITION NODE] {input_value} + {value_to_add} = {result}")
        
        return {
            "value": result,
            "operation": f"{input_value} + {value_to_add} = {result}",
            "status": "success",
            "node_name": context.get('node_name', 'Unknown')
        }

def module():
    return AdditionNode()
