## Motivation

At the time of writing, the text search of Tori.fi is very primitive and doesn't seem to have any AI capabilities. Queries are not translated and query words are not stemmed, meaning that a query of "puu" (wood in English) will not return a listing that contains the word "puinen" (wooden in English).

In addition, images in listings are not used when matching listings to queries. While typically listing images in Tori are not of the best quality, there are cases where the images do contain useful information that is not available in the text description.

Naturally, adding these capabilities would introduce costs that Tori is likely not willing to pay for. This is totally understandable as their goal is to make money.

This project is an proof of concept of utilizing modern AI technologies for searching Tori listings with one important self-imposed restriction. **Running the project should not cost anything**. I wanted to see how far one can get with free tier Azure services.

## Results

Turns out that not very far.

The web app and database queries are slow and the search is not very accurate which combined make the user experience suboptimal. The fixes to these problems are simple: Paying to scale up the web app and the database would mean faster response times. Paying for a better model, e.g. Azure OpenAI, would mean better embeddings and hence better matching. But because of the no-cost restriction, these fixes were not implemented.

The success story of this project came from translations. Most of the listings in Tori are in Finnish which means that English queries on the site don't get good results. With this project, queries in English and Finnish are served equally because user queries are translated to Finnish prior to matching. Azure AI Translation free tier comes with 2 million free characters per month, which is more than enough for this use case.

## Takeaways

- Azure SQL Database was first considered as the database solution for this project. The free Azure SQL Database offer comes with a serverless instance with 100 000 vCore seconds (1667 minutes) per month and 32 GB of storage which appears to be very generous. BUT it will auto-pause after some time of inactivity. The database will auto-resume on its own once a query is made but resuming can take up to 60 seconds during which the database is not available. Whether the auto-pause and auto-resume durations are counted towards the allowance is unclear. But in any case, this downside was not acceptable and I ended up going with Azure Cosmos DB.
- Some Azure services are seemingly free to use but end up sneakingly billing customers. An example of this is Azure Functions. They have a free monthly allowance of 1 million minutes of execution time. BUT! Azure Functions require an Azure Storage Account to operate (for storing logs, state, etc.). And Azure Storage accounts are not free.
- I wanted to see how well a Finnish model would generated embeddings which is why translation was not done prior to embedding scraped listings. The results were adequate at best. The search accuracy could likely be improved by translating listings to English prior to embedding and then translating user queries to English prior to matching.