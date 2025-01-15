def generate_cypher_eval_prompt(cypher: str, model: str) -> str:
    # provides the prompt for auomatically evaluating the cypher query
    return """
    You are a highly intelligent assistant. Your job is to evaluate cypher queries against a model cypher query.
    Ignore any escape sequences but pay attention to the direction of the relationships.
    If the cypher query matches the model exactly, return 1.
    If the cypher query and the model are not the same, return -1.
    If the cypher query is None, return -1.
    
    IMPORTANT: Only answer with a single number (1, -1). Do not add any text, explanations, or comments.

    ### Example 1: 
    Cypher: \n\nMATCH (p:Project {{name: "CDPKit"}})-[:INCLUDED_IN]->(f:Folder) RETURN f.name
    Model: \\n\\nMATCH (f:Folder)-[:INCLUDED_IN]->(p:Project {{name: 'CDPKit'}}) RETURN f.name
    Answer: -1

    ### Example 2:
    Cypher: \n\nMATCH (f:File)-[:INCLUDED_IN]->(fld:Folder {{name: "Base"}}) RETURN f.name
    Model: \\n\\nMATCH (f:File)-[:INCLUDED_IN]->(folder:Folder {{name: 'Base'}}) RETURN f.name
    Answer: 1

    Cypher: {cypher}
    Model: {model}
    """.format(cypher = f"{cypher}", model = f"{model}")

def generate_context_eval_prompt(context: str, model: str) -> str:
    # provides the prompt for auomatically evaluating the context
    return """
    You are a highly intelligent assistant. Your job is to evaluate a retrieved context against a model context.
    Ignore any formatting.
    If the context matches the model return 1.
    If the context is empty except for placeholders or it says that the context could not be retrieved return 0.
    If the context provides info that is not in the model, return -1.
    
    IMPORTANT: Only answer with a single number (1, -1, 0). Do not add any text, explanations, or comments.

    ### Example 1: 
    Context: [['f.name']]
    Model: ['f.name'], ['Chem'], ['Pharm'], ['Base'], ['Biomol'], ['ConFGen'], ['ConfGen'], ['Descr'], ['ForceField'], ['GRAIL'], ['Grid'], ['Math'], ['MolProp'], ['Shape'], ['Util'], ['Vis']
    Answer: 0

    ### Example 2: 
    Context: [['p.name'],['FragmentList']]
    Model: ["p.name"],["FragmentList"]
    Answer: 1
    
    ### Example 3:
    Context: [["p.name","p.type"],["bond",""Chem.Bond""]]
    Model: ['f.returns'], ['{{type: "int", "comment": ""}}']
    Answer: -1
    

    Context: {context}
    Model: {model}
    """.format(context = f"{context}", model = f"{model}")


def generate_answer_eval_prompt(question: str, answer: str, context: str) -> str:
    # provides the prompt for auomatically evaluating the answer based on the context
    return """
    You are a highly intelligent assistant. Your job is to evaluate if an answer correclty answers a question based on the retrieved context. Ignore any python code examples in the answer.
    Ignore any formatting.
    If the answer says it correctly cant answer based on the context return 2.
    If the answer says it wrongly cant answer based on the context even tho the answer would be in the context return 0.
    If the answer positively provides the questioned information based on the context return 1. 
    If the answer provides information that is not present in the context, return -1.
    
    IMPORTANT: Only answer with a single number (1, -1, 0, 2). Do not add any text, explanations, or comments.

    ### Example 1: 
    Question: What are the folders included in the CDPKit Project?
    Context: f.name
    Answer: The CDPKit Project includes the following folder:\n\n- [f.name] (The specific name of the folder is not provided in the retrieved context.) \n\nGiven the limited information, we can only state that there is at least one folder included in the CDPKit Project
    Evaluation: 2

    ### Example 2: 
    Question: What class does the class AromaticRingSet inherit from?
    Context: [['p.name'],['FragmentList']]
    Answer: The class AromaticRingSet inherits from FragmentList.
    Score: 1
    
    ### Example 3:
    Question: What class does the class AromaticRingSet inherit from?
    Context: [['p.name'],['FragmentList']]
    Answer: I cannot answer this based on the provided context.
    Score: 0

    ### Example 4:
    Question: How to generate Conformations with the class ConformerGenerator??
    Context: f.name, f.comment
    Answer: To generate conformations using the `ConformerGenerator` class, you can use the method `generateConformations`.
    Score: -1
    

    Question: {question}
    Context: {context}
    Answer: {answer}
    """.format(question = f"{question}", context = f"{context}", answer = f"{answer}")

def generate_code_eval_prompt(answer: str) -> str:
    # provides the prompt for auomatically evaluating the code example
    return """
    You are a highly intelligent assistant. Your job is to evaluate if the python code provided in a text is syntactically correct. 
    Ignore any formatting.
    If it is correct return 1. 
    If the text does not contain a code example return 2. 
    If the code example is syntactically incorrect or contains a cypher query return -1
    
    IMPORTANT: Only answer with a single number (1, -1, 2). Do not add any text, explanations, or comments.
    
    ### Example 1: 
    Text: The class AromaticRingSet inherits from FragmentList. \n\nPython example:\n```python\n# This is how you might represent the inheritance relationship in Python\nclass AromaticRingSet(FragmentList):\n    pass\n```
    Score: 1

    Text: {answer}
    """.format(answer = f"{answer}")

def generate_overall_eval_prompt(answer: str, model: str) -> str:
    # provides the prompt for auomatically evaluating the overall answer of the RAG
    return """
    You are a highly intelligent assistant. Your job is to evaluate if an answer matches a model answer.
    Ignore any formatting or python code.
    If the answer and the model both say they cannot answer something, return 2. 
    If the answer and the model match, return 1
    If the answer does not match the model but rather provides wrong information, return -1. 
    If the answer says it cannot answer something, but the model can, return 0.
    
    IMPORTANT: Only answer with a single number (1, -1, 0, 2). Do not add any text, explanations, or comments.

    ### Example 1: 
    Answer: The CDPKit Project includes the following folder:\n\n- [f.name] (The specific name of the folder is not provided in the retrieved context.) \n\nGiven the limited information, we can only state that there is at least one folder included in the CDPKit Project
    Model: The folders included in the CDPKit Project are:\\n- Chem\\n- Pharm\\n- Base\\n- Biomol\\n- ConfGen\\n- Descr\\n- ForceField\\n- GRAIL\\n- Grid\\n- Math\\n- MolProp\\n- Shape\\n- Util\\n- Vi",
    Evaluation: 0

    ### Example 2:
    Answer: The class AromaticRingSet inherits from FragmentList. \n\n```python\n# Example of accessing the inherited class in Python\nclass AromaticRingSetInheritance:\n    def __init__(self):\n        self.inherited_class = \"FragmentList\"\n        \n# Usage\naromatic_ring_set = AromaticRingSetInheritance()\nprint(aromatic_ring_set.inherited_class)\n``` 
    Model: The class AromaticRingSet inherits from FragmentList. 
    Score: 1
    
    ### Example 3:
    Answer: The parameter `feature` of the function `hasHydrophobicity` stands for \"Feature\". There is no additional comment or default value specified for this parameter. Here is how you might use this parameter in a simple example:\n\n```python\n# Assuming there is a way to call hasHydrophobicity with parameters\nresult = hasHydrophobicity(feature=\"some_value\")\n```\n\nIn this example, `\"some_value\"` would be the value passed to the `feature` parameter. However, note that the exact usage and valid values for the `feature` parameter would depend on the implementation of the `hasHydrophobicity` function.
    Model: I cannot tell what it stands for.
    Score: 2

    ### Example 4:
    Answer: To generate conformations using the `ConformerGenerator` class, you can use the method `generateConformations`.
    Model: To generate conformations using ConformerGenerator, you can use the `generate` method. Here's how you can do it: - `generate`: Generates conformations.
    Score: -1
    

    Answer: {answer}
    Model: {model}
    """.format(answer = f"{answer}", model = f"{model}")