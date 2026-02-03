"""Prompt templates for NewsInteractAction.

This module provides the prompt templates used by NewsInteractAction:
- Directive template for formatting retrieved context
- Intent extraction template for parsing user queries
"""
# ============================================================================
# Intent Extraction Template
# ============================================================================

INTENT_EXTRACTION_TEMPLATE = """Analyze the user's request to determine their intent regarding news retrieval.

Extract the following information:
1. source: Specific news source requested. If none, do not return a source. the list of sources are: {sources}
2. query: If the user is asking for a specific detail specify what they are asking for. Asking for news, the happenings in the country or similar general statements is not a query.
   Queries concerning time should be extracted as a date_filter, not a query.
   Notable words that would result in a query include: arrests, murders, killings, shootings, crime, politics, sportsetc.
3. date_filter: If a specific date or time range is mentioned (e.g., "today", "yesterday"), extract it in the format: YYYY-MM-DD. The current date is {current_date}

Return the result as a JSON object with that only contains the keys that you extracted information for.
If nothing was extracted, return an empty JSON object.
"""

# ============================================================================
# Summary Template
# ============================================================================


DAILY_SUMMARY_TEMPLATE = """
TASK DESCRIPTION:
Return a concise summary in essay form of at most 65 words based on the titles given below as well as a list of links to the articles from which information was used to create the summary.
Note the following instructions:
1. Avoid international news about things that are not relevant to Guyana.
2. Write the summary in a relaxed tone as if you are explaining as much as you can to a friend as quickly as possible.
3. Do not add in greetings or farewells Start off with something along the lines of or "In the news for {current_date}". Do not include the time.
4. Avoid highlighting a specific article and instead provide a general summary of as many articles as possible.
5. Prioritize mentioning what you would consider being the most important news from multiple categories such as politics, crime, oil and gas, etc.
6. Note the links of the articles from which information was used to create the summary determine the topic of the link.
7. If there are multiple news titles pertaining to something mentioned in the summary, include all of the relevant links about the topic in the links section.
8. Return the links formatted as: "[topic of link 1 in less than 3 words in Title Case](short link to article 1)", "[topic of link 2 in less than 3 words in Title Case](short link to article 2)", ....

Return the result as a JSON object with the following keys:
- summary: The summary based on the titles.
- links: A list of links to the articles from which information was used to create the summary.

NEWS TITLES:
{results}
"""

SUMMARY_TEMPLATE = """The following are news articles.

{results}
Create a summary in essay form of at most 65 words based on the user request.
Add the links of the articles that were used to create the summary, at the end of the summary.

If the user has not specified any particular topic or content follow the rules below:
  - Return a concise summary in essay form of at most 65 words based on the titles of the news articles.
  - If there are multiple news titles pertaining to something mentioned in the summary, include all of the relevant links about the topic in the links section

The links should be formatted as: "[topic of link 1 in around 2 words in Title Case](short link to article 1)", "[topic of link 2 in around 2 words in Title Case](short link to article 2)", ....
The topic for the links should be derived from the title or content of the article.

If no relevant news articles are found, simply say so and apologize.
"""



# ============================================================================
# Directive Template
# ============================================================================

DIRECTIVE_TEMPLATE = """Present the following to the user in a relaxed and natural tone.

{summary}

Append the links to the articles that were used to create the summary at the end of the summary."""

LINKS_TEMPLATE = "Present the following links as a bulleted list without any additional text or formatting: {links}"
