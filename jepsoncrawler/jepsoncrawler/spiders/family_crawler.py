import scrapy
import logging
import pathlib

from yaml_pyconf import SimpleConfig

CONFIG = SimpleConfig(pathlib.Path(__file__).parents[2].joinpath("config.yaml"))

class JepsonFamilyCrawler(scrapy.Spider):
    name = "jepson-family-crawler"

    start_urls = [CONFIG.crawler_start_url]

    def parse(self, response, family=None, genus=None, species=None):
        """
        The parser uses visual elements on the page to navigate, and makes
        no assumptions about URL structure.
        :param response: the response to parse
        :param family: Continue crawl from family-level taxon or key page
        :param genus: Continue crawl from genus-level taxon or key page
        :param species: Extract and yield species description
        :return: Next crawl or extracted species-level information
        """
        if not family and not genus and not species:  # Top Level
            for family_name in CONFIG.family_keys:
                # Follow links from the top-level page
                link = response.xpath(f"//a[contains(text(), '{family_name}')]/@href").get()
                if link:
                    logging.info(f"now crawling family {family_name}")
                    yield response.follow(link, callback=self.parse, cb_kwargs={"family": family_name})

        # Crawling an individual Family
        elif family:
            link = response.xpath(f"//a[contains(text(), 'Key to')][i[contains(text(), '{family}')]]/@href").get()
            if link:  # Indicates we are on the taxon page and need to get to the key page
                logging.info(f"going from family {family} taxon page to key page")
                yield response.follow(link, callback=self.parse, cb_kwargs={"family": family})
            else:  # We are on the key page and need to start crawling genera
                base_query = "//a[contains(text(), '.....\xa0')]"
                links = response.xpath(f"{base_query}/@href").getall()
                raw_names = response.xpath(f"{base_query}/text()").getall()
                genera = [name.split("\xa0")[-1].title() for name in raw_names]

                for genus_name, link in zip(genera, links):
                    logging.info(f"now crawling genus {genus_name}")
                    yield response.follow(link, callback=self.parse, cb_kwargs={"genus": genus_name})

        elif genus:
            link = response.xpath(f"//a[contains(text(), 'Key to')][i[contains(text(), '{genus}')]]/@href").get()
            logging.info(f"Genus key page link is {link}")
            if link:  # Get to genus key page
                logging.info(f"now going from genus {genus} taxon to key page")
                yield response.follow(link, callback=self.parse, cb_kwargs={"genus": genus})
            else:  # Start crawling species
                base_query = "//a[contains(text(), '.....\xa0')]"
                links = response.xpath(f"{base_query}/@href").getall()
                raw_names = response.xpath(f"{base_query}/text()").getall()
                specieses = [x.split("\xa0")[-1].replace(f"{genus[0]}.", genus) for x in raw_names]

                for species_name, link in zip(specieses, links):
                    logging.info(f"now crawling species {species_name}")
                    yield response.follow(link, callback=self.parse, cb_kwargs={"species": species_name})

        elif species:  # We made it! Use <b> tags to identify structured characteristics
            parsed_data = {
                "family": response.xpath("//b[contains(text(), 'Family: ')]/text()").get().split("Family: ")[-1],
                "genus": response.xpath("//b[contains(text(), 'Genus: ')]/text()").get().split("Genus: ")[-1],
                "species": species,
            }

            # This gets everything from the description that's in bold
            fields = response.xpath("//div[@class='bodyText']/b/text()").getall()

            # This gets the stuff that's not in bold and splits it up
            values = response.xpath("//div[@class='bodyText']/text()").getall()

            parsed_data["local_status"] = fields[0]

            fields = fields[1:]

            for k, v in zip(fields, values):
                parsed_data[k] = v
            logging.info(f"successfully parsed species {species}")
            yield parsed_data
