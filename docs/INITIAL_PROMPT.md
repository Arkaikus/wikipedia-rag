you are an engineering lead that is planning for the development of a small mvp, this mvp targets to be a chatbot that use rag on any given wikipedia page, that way the chatbot can answer questions focused on a very specific subject, making documented responses.

please write a TODO.md with a roadmap of development for the mvp in python, the mvp should work locally at first with lmstudio but have the posibility of migrating to cloud services through adapters, think of a way to retrieve or scrap a given wikipedia page to start the chat, use a self hosted vector db like weaviate or chroma in a docker compose stack 

for future development consider the use of browser mcp to get the data from the browser

---

I like how it's going, let's do a small adjustment before getting started with the implementation, lets use uv to manage the python project and dependencies