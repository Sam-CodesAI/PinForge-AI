"""PinForge AI — Media RSS Feed Generator for Pinterest Auto-Publishing.

Generates valid RSS 2.0 / Media RSS XML feed with <enclosure> tags.
Pinterest Business accounts can connect this feed directly to auto-publish
Pins without developer API reviews or token expirations.
"""

import html
from datetime import datetime, timezone
from typing import List
from xml.etree import ElementTree as ET

from python_engine.config import BASE_URL
from python_engine.models import ScheduleItem


def generate_pinterest_rss(items: List[ScheduleItem], feed_title: str = "PinForge AI Curated Finds") -> str:
    """Generate valid Media RSS 2.0 XML string for Pinterest Auto-Publish."""
    rss = ET.Element("rss", {
        "version": "2.0",
        "xmlns:media": "http://search.yahoo.com/mrss/",
        "xmlns:atom": "http://www.w3.org/2005/Atom",
    })

    channel = ET.SubElement(rss, "channel")

    title_el = ET.SubElement(channel, "title")
    title_el.text = feed_title

    link_el = ET.SubElement(channel, "link")
    link_el.text = BASE_URL

    desc_el = ET.SubElement(channel, "description")
    desc_el.text = "Automated high-converting Amazon and Pinterest curated finds with FTC disclosures."

    lang_el = ET.SubElement(channel, "language")
    lang_el.text = "en-us"

    pub_date_el = ET.SubElement(channel, "pubDate")
    pub_date_el.text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    atom_link = ET.SubElement(channel, "atom:link", {
        "href": f"{BASE_URL}/feed.xml",
        "rel": "self",
        "type": "application/rss+xml",
    })

    for item in items:
        entry = ET.SubElement(channel, "item")

        i_title = ET.SubElement(entry, "title")
        i_title.text = item.title[:100]

        i_link = ET.SubElement(entry, "link")
        i_link.text = item.link

        i_desc = ET.SubElement(entry, "description")
        i_desc.text = item.description[:500]

        i_guid = ET.SubElement(entry, "guid", {"isPermaLink": "true"})
        i_guid.text = item.link

        # Pinterest requires enclosure or media:content for image
        ET.SubElement(entry, "enclosure", {
            "url": item.image_url,
            "type": "image/jpeg",
            "length": "100000",
        })

        ET.SubElement(entry, "media:content", {
            "url": item.image_url,
            "medium": "image",
            "type": "image/jpeg",
        })

        i_pub = ET.SubElement(entry, "pubDate")
        try:
            dt = datetime.fromisoformat(item.published_at.replace("Z", "+00:00"))
            i_pub.text = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except Exception:
            i_pub.text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

        category_el = ET.SubElement(entry, "category")
        category_el.text = item.board_name

    xml_str = ET.tostring(rss, encoding="utf-8", xml_declaration=True).decode("utf-8")
    return xml_str
