import scrapy
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
                    yield response.follow(link, callback=self.parse, cb_kwargs={"family": family_name})

        # Crawling an individual Family
        elif family:
            link = response.xpath(f"//a[contains(text(), 'Key to')][i[contains(text(), '{family}')]]/@href").get()
            if link:  # Indicates we are on the taxon page and need to get to the key page
                yield response.follow(link, callback=self.parse, cb_kwargs={"family": family})
            else:  # We are on the key page and need to start crawling genera
                base_query = "//a[contains(text(), '.....\xa0')]"
                links = response.xpath(f"{base_query}/@href").getall()
                raw_names = response.xpath(f"{base_query}/text()").getall()
                genera = [name.split("\xa0")[-1].title() for name in raw_names]

                for genus_name, link in zip(genera, links):
                    yield response.follow(link, callback=self.parse, cb_kwargs={"genus": genus_name})

        elif genus:
            # There's a dropdown, so we can go straight to species from here
            links = response.xpath("//option/@value").getall()
            species_names = response.xpath("//option/text()").getall()

            for species_name, link in zip(species_names, links):
                if link != "None":
                    yield response.follow(link, callback=self.parse, cb_kwargs={"species": species_name})

        elif species:  # We made it! Use <b> tags to identify structured characteristics
            parsed_data = {
                "url": response.url,
                "family": response.xpath("//b[contains(text(), 'Family: ')]/text()").get().split("Family: ")[-1],
                "genus": response.xpath("//b[contains(text(), 'Genus: ')]/text()").get().split("Genus: ")[-1],
                "species": species,
            }

            # This gets everything from the description that's in bold
            fields = response.xpath("//div[@class='bodyText']/b/text()|//div[@class='bodyText']/b/a/text()").getall()

            # This gets the stuff that's not in bold and splits it up
            values = response.xpath("//div[@class='bodyText']/text()").getall()

            parsed_data["local_status"] = fields[0]

            fields = fields[1:]

            for k, v in zip(fields, values):
                parsed_data[k] = v
            yield parsed_data
