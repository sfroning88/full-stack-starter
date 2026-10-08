# **Full Stack AI Engineer: A Modern Day Polymath**

Anyone who has worked in a team environment knows that every successful team has one go-to person—that special individual who can help you regardless of the nature of your problem. On a traditional software development team, this individual is an expert programmer and is also an expert in one other technology, which could be a database technology like Snowflake or an important framework like Springboot. However, what makes this person special is that they know a fair amount about a lot of other technology in their organization’s infrastructure and development environment. For example, they know their way around Kubernetes, understand networking, are fluent in architectural design patterns, and may have even coded a few user interfaces. While they may not be an expert in these other technologies, they know enough to figure out hard problems, and if they had to, they could become an expert.

The benefits of being multidisciplinary go beyond problem-solving skills. There are many other benefits that they enjoy and that their team benefits from:

- They make more money, and employers like to keep these people around. They also make less skilled workers more productive and do more work themselves.
- They adapt to change better. If they want to change the focus of their career, they can do so quickly. Many AI/ML engineers today were not formally trained at a university—rather, they learned on their own.
- They lead. When their team needs to change focus or tackle a hard problem they can lead the way since they have a solid working knowledge of where the team needs to go anyway.
- They tend to be more innovative. This is not a coincidence. Awareness of a solution's entire stack equips you with the knowledge to see a good idea that would elude someone who is narrowly focused.
- They facilitate collaboration by bridging the gap between specialized teams.

This post suggests AI/ML-related topics that, once studied, could guide you into becoming a full-stack AI Engineer. But before presenting these topics, let’s get a historical understanding of the impact of multidisciplinary skills. It turns out that the profile I described above is not unique to the software industry. In Science, Art, and Philosophy, such a person is called a Polymath. Just for fun, let’s review a few Polymaths through the ages.

## **Polymaths Through the Ages**

Leonardo da Vinci (1452 \- 1519\) is the most famous Polymath. He is a household name, and his life works are well known. He painted the Mona Lisa and The Last Supper, furthered our understanding of anatomy by dissecting bodies, and designed flying machines and robots.

Ada Lovelace (1815 \- 1852\) was an English mathematician, writer, and the world’s first computer programmer. At an early age, she excelled at mathematics, which earned her an opportunity to work with Charles Babbage \- another English mathematician. She is chiefly known for her work on Charles Babbage's Analytical Engine, which was basically a mechanical computer. While translating documentation of the Analytical Engine, she added a few “Notes” of her own, and one of her notes, Note G (sometimes called the 7th Note), is considered the first program ever written. She was also the first to recognize that the machine had applications beyond pure calculations \- her “poetical science” resulted in musings about how technology could be used as a collaborative tool.

George Washington Carver (1864 \- 1943\) \- was an agricultural scientist, botanist, inventor and educator. Carver's contributions to the fields of agriculture and environmental science forever transformed the landscape of American farming and laid the foundation for modern sustainable practices. He pioneered the concept of crop rotation and soil conservation at a time when farmers were struggling. His work facilitated soil rejuvenation, allowing farmers to increase productivity. As an inventor, he figured out how to make the most of peanuts by inventing peanut butter. (By the way, a peanut is not a nut. It is a legume.)

Now that we understand the impact of multidisciplinary skills and have historical examples of Polymaths from the arts and sciences let’s apply these ideas to modern times and see what it takes to be a Full-Stack AI Engineer.

## **AI Data Infrastructure**

AI is all about data \- so to be a full-stack AI Engineer, you need to understand AI Data Infrastructure.

### _Modern Datalake_

The Modern Datalake \- If your employer is getting serious about AI/ML, they will be coming to you for advice on how to modernize existing infrastructure. A Modern Datalake is a storage solution capable of holding all data needed for AI/ML, including structured and unstructured data. Consequently, a Modern Datalake is one part Data Lake for unstructured data and one part Data Warehouse for structured data. What makes a Modern Datalake powerful is that it uses high-speed, scalable object storage under the hood for all data types \- unstructured and structured.

The use of object storage for both the Data Lake and the Data Warehouse is made possible by the rise of Open Table Formats (OTFs) like Apache Iceberg, Apache Hudi, and Delta Lake, which are specifications that, once implemented, make it seamless for object storage to be used as the underlying storage solution for a data warehouse. These specifications also provide features that may not exist in a conventional Data Warehouse \- for example, snapshots (also known as time travel), schema evolution, partitions, partition evolution, and zero-copy branching.

A Modern Datalake Reference Architecture can be found here. A companion paper showing how this architecture supports all AI/ML workloads is here.

### _Machine Learning Operations (MLOps)_

Machine Learning Operations (MLOps) \- MLOps is to AI/ML what DevOps is to application development. To better understand the importance of MLOps, it is helpful to compare model creation to conventional application development.

Conventional application development, like implementing a new microservice that adds a new feature to an application, starts with reviewing a specification. Any new data structures or any changes to existing data structures are designed first. The design of the data should not change once coding begins. The service is then implemented, and coding is the main activity in this process. Unit tests and end-to-end tests are also coded. These tests prove that the code is not faulty and correctly implements the specification. They can be run automatically by a CI/CD pipeline before deploying the entire application.

Creating a model and training it is different. An understanding of the raw data and the needed prediction is the first step. ML engineers do have to write some code to implement their neural networks or set up an algorithm, but coding is not the dominant activity. Repeated experimentation is the main activity. During experimentation, the design of the data, the design of the model, and the parameters used will all change. After every experiment, metrics are created that show how the model performed as it was trained. Metrics are also generated for model performance against a validation set and a test set. These metrics are used to prove the quality of the model. You can save the model itself after every experiment. Once a model is ready to be incorporated into an application, it needs to be packaged and deployed.

MLOps tools can take care of the core features described above. Many can do much more. Three notable MLOps tools that should be considered for your projects are:

- Kubeflow \- from Google
- MLflow \- from Databricks
- MLRun \- from McKinsey and Company

### _Distributed Training_

Distributed Training \- Distributed model training refers to the process of training machine learning models across multiple computational devices or nodes simultaneously. This approach expedites the training process, particularly for large datasets and complex models that require substantial computational resources.

Two notable frameworks for distributed training are:

Ray \- Ray is an open-source framework for all things distributed. It runs on virtual machines and Kubernetes. You can also prototype with it on your local development machine as long as you do not use too many workers and you are not doing anything too complicated. It supports both TensorFlow and PyTorch. For a managed instance of Ray, check out Anyscale.

TorchDistributor is a library for distributing PyTorch based machine learning workloads on Apache Spark. The spark-tensorflow-distributor can be used for TensorFlow based machine learning. Both can be run in a host environment on Databricks.

### _Vector Databases_

Vector Databases \- All models require numbers as inputs and produce numbers as outputs. This simple fact places a few additional requirements on your AI data infrastructure if you are interested in Generative AI, where words have to be turned into numbers \- or vectors. A vector database indexes, stores, and provides access to your documents alongside their vector embeddings, which are numerical representations of your documents. Vector databases facilitate semantic search, which is needed for Retrieval Augmented Generation (RAG) \- a technique utilized by generative AI to marry information in your custom corpus to an LLMs trained parametric memory.

Three Vector Databases worth researching are:

- Pinecone
- Milvus
- Weaviate

Related: MLOps Architecture Guide for AI Infrastructure

## **AI/ML Engineering**

Armed with a working knowledge of your AI data infrastructure, you will next need to understand tooling around model building. This is what I refer to as AI/ML Engineering. In the old days, before generative AI, there was supervised learning, unsupervised learning, reinforcement learning and natural language processing (NLP). However, with the rise of ChatGPT, a new category was created known as Generative AI, and everything else is now referred to as “Traditional AI.”

Before getting into the tooling for AI Engineering, let’s look at these two categories of AI.

### _Traditional AI_

Traditional AI includes model types that are as valuable to your business as generative AI. This includes models created via unsupervised learning, where you look for patterns in unlabeled data. Reinforcement learning is another type of AI where models that interact with the environment are created. Finally, traditional AI includes supervised learning, where the relationship between input data and output labels is known during training. With supervised learning, you will have a test set for testing your models to come up with a precise accuracy measure.

### _Generative AI_

As the name suggests, generative AI is about generating new data. Models used as chatbots fall into this category and are known as Large Language Models (LLMs). With generative AI you will not have a formal training set, validation set, and test set. Rather, you will have a custom corpus that you can use to fine-tune your LLM. Retrieval Augmented Generation, first proposed by Meta, is another technique for using a custom corpus and a vector database with an LLM.

### _Machine Learning Frameworks_

PyTorch and TensorFlow are the top two machine learning frameworks for building neural networks today. PyTorch is a bit more popular than TensorFlow. These frameworks can be used for both traditional and generative AI. However, the one you choose to learn should be based on the framework in use by your employer. They have more in common than differences. Since architecting models requires more knowledge of training techniques than coding techniques, you will find that it is easy to switch between frameworks if needed.

If you need to get something into production quickly, consider scikit-learn. Scikit-learn uses algorithms to create models. You do not need to design and code a neural network. Consequently, using Scikit-learn, you can quickly build an adequately performing model that could be used as a first-version model within an AI solution. From there, you can build a better-performing neural network using either PyTorch or TensorFlow, which often takes more time.

### _Open Source Communities and Tools_

Open-source LLMs have democratized generative AI. Furthermore, using platforms like HuggingFace, you can gain access to a large collection of models designed and trained for a variety of tasks, such as summarization, question-answering, translation, and entity recognition. HuggingFace also provides a library that allows you to easily use LLMs.

To streamline the integration of LLMs within applications, you will need to learn a framework like LangChain. LangChain simplifies tasks such as retrieving data, creating agents, retrieval augmented generation, and creating prompts.

## **Conclusion**

The Full-Stack AI Engineer possesses skills that encompass software development, machine learning, and data infrastructure. They are proficient in MLOps and distributed training and can use frameworks like TensorFlow, PyTorch, or Scikit-learn to design and train models for traditional AI and generative AI. Finally, a full-stack AI Engineer should have a mindset of continuous learning to stay up to date with evolving technologies for AI data infrastructure and AI/ML engineering.
