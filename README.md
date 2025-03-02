graphRAG
==============================

**A Graph RAG System for the CDPKit**

## Table of Contents

- [About](#about)
- [Getting Started](#getting-started)
    - [Installation](#installation)
    - [Build the Knowledge Graph](#build-the-knowledge-graph)
    - [Pretrained Large Language Models](#pretrained-large-language-models)
    - [Basic Usage](#basic-usage)
        - [Graph RAG Dashboard](#graph-rag-dashboard)
        - [Direct Usage of the Graph RAG System from the Command Line](#direct-usage-of-the-graph-rag-system-from-the-command-line)
- [Copyright](#copyright)
    - [Acknowledgments](#acknowledgements)

## About

This code provides a Graph RAG system for the cheminformatics toolkit [CDPKit](https://cdpkit.org/) based on its Python API documentation. A Graph RAG system is Retrieval Augmented Generation that uses a Knowledge Graph as its external knowledge base. 
The system is capable of answering general questions about the CDPKit and its structure, as well as providing basic code snippets in Python.  
The Knowledge Graph is a Neo4j Knowledge Graph hosted on [Neo4j AuraDB](https://neo4j.com/product/auradb/).  
The Graph RAG System works by taking the user query and passing it on to [CodeLlama-13b-Instruct-hf](https://huggingface.co/codellama/CodeLlama-13b-Instruct-hf), which translates it into a Cypher query. The Cypher query is then used to directly query the Knowledge Graph for the relevant information to the user query, and together they are passed to [Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct), which answers the original user query based on the retrieved context. It will also try to provide a relevant code snippet in Python that showcases the usage of the retrieved context.  
The Graph RAG system can be used both in form of a dashboard, or within the command line. 


## Getting started

This short guide will help you get started with the Graph RAG system. 

### Installation

Run the following command to copy the repository to your local system and to install the necessary dependencies: 

```
git clone https://github.com/molinfo-vienna/graphRAG.git
cd graphRAG
pip install -r requirements.txt
```

### Build the Knowledge Graph

This step can be skipped if you already have your Neo4j AuraDB instance with the Knowledge Graph.  
Otherwise, create an account and AuraDB instance [here](https://login.neo4j.com/u/login/identifier?state=hKFo2SBvUEdWaDNkeTUwd3ZWUVhEQlJoQ21KZEJfbXR4c2N6S6Fur3VuaXZlcnNhbC1sb2dpbqN0aWTZIHpWdXpsRHBieTgwRzZvOXh5WVdiQWhjNUpHek1fUjRto2NpZNkgV1NMczYwNDdrT2pwVVNXODNnRFo0SnlZaElrNXpZVG8).  
Once this is done, set your Neo4j uri, user and password as environment variables. 
To do so once for the current shell and all processes started from it, execute 

```
export NEO4j_URI="yourvalue"
export NEO4j_USER="yourvalue"
export NEO4j_PASSWORD="yourvalue"
```
If you want to add this to your environment permanently for all future bash sessions as well (recommended), go to your $HOME directory and add these lines to your .bashrc file.
Your Neo4j credentials will also be need to be set as an environment variable for later use of the Graph RAG.  
Next, you need to copy the [CDPKit Python API documentation](https://github.com/molinfo-vienna/CDPKit/tree/master/Doc/Doxygen/Python-API/Source/CDPL) to a local directory and again set the path to the documentation as an environment variable:

```
export CDPKit_PATH="path/to/your/directory/CDPKit/Doc/Doxygen/Python-API/Source/CDPL/"
``` 
To create the Knowledge Graph in your AuraDB instance, make sure to set all necessary environment variables and then run: 

```
python knowledgeGraph/KnowledgeGraphManager.py
```

### Pretrained Large Language Models 

The Graph RAG system works by using pretrained LLMs from [huggingface](https://huggingface.co/). Set

```
export MODEL_LOCATION="/path/to/local/directory"
```
in your .basrc file as the location where the pretrained models should be downloaded and stored. This will take around **40GB** of space on your disk. When running the Graph RAG system for the first time, it will download the models to your specified location once.  
**Further, to ensure optimal performance, it is recommended to run the Graph RAG system on a machine that is equipped with one or more GPUs.** 

### Basic Usage

#### Graph RAG Dashboard 

Once the Knowledge Graph is created and all variables have been set accordingly, this repository provides access to user friendly [Dash](https://dash.plotly.com/) dashboard that can be hosted by running 

```
python graphRAG/graphRag_dashboard.py
```
It has a chat-like interface with example questions and can be used to directly question the system about the CDPKit.

![dashboard](graphRAG/images/dasboard_image.png)

#### Direct Usage of the Graph RAG System from the Command Line 

To directly query the Graph RAG system from the command line, run

```
python graphRAG/graphRAG.py "What methods does the class AtomBondMapping have?"
```


## Copyright

Copyright (c) 2024, Selina Schöndorfer


#### Acknowledgements
 
Project structure based on the 
[Computational Molecular Science Python Cookiecutter](https://github.com/molssi/cookiecutter-cms) version 1.1.
