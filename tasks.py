from pathlib import Path

from robocorp import log
from robocorp import workitems
from robocorp.tasks import task
from latimes_scrapper import LaTimesScrapper


@task
def producer():
    """Produce input Work Items for the next step."""
    log.info("Producer task started.")

    # Create a LA Times webscrapping task, informting the search term, list of topics and the number of articles to be scrapped
    webscrapping_task = {
        "search_term": "GPT",
        "topics": ["Technology and the Internet", "Politics"],
        "number_of_months":12
    }
    workitems.outputs.create(webscrapping_task)



@task
def consumer():
    """
    Process all the produced input Work Items from the previous step.
    Will open the website, perform the extractions and save the excel file with the data
    Saves the images in the output folder
    """
    
    log.info("Consumer task started")

    for item in workitems.inputs:

        search_term = item.payload["search_term"]
        topics = item.payload["topics"]
        number_of_months = item.payload["number_of_months"]

        latimes_scrapper = LaTimesScrapper(search_term, topics, number_of_months)
        
        try:
            latimes_scrapper.run()
            item.done()
        except Exception as e:
            latimes_scrapper.close_website()
            item.fail(
                exception_type="APPLICATION",
                code="UNEXPECTED_ERROR",
                message="An error occurred while processing the webscrapping data",
            )
            continue

