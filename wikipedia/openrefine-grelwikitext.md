# How to create a GREL instruction to generate template Wikitext in OpenRefine
[OpenRefine](https://openrefine.org/) lets you transform values in all sorts of ways using little snippets of Javascript or General Refine Expression Language (GREL). You can link together simple instructions to do some really complex changes.

[Expressions in OpenRefine](https://openrefine.org/docs/manual/expressions)

This page tells you how to add a formatted table of descriptive metadata to images when you load them to Wikimedia Commons using OpenRefine.

You’re going to use GREL to build Wikitext from other values in your project, which in turn can be used by your selected template to display a populated table of data on each image’s page. Write this up in a text editor like Notepad++ or Sublime Text first – it’s a lot easier to edit there.

The main structure of the instruction looks like this:

```
"== {{int:filedesc}} ==\n" +
"{{TePapaColl\n" +

*Your field instructions go here!*

"}}\n" +
"=={{int:license-header}}==\n" +
"{{cc-by-4.0}}\n" +

*Your category instructions go here!*
```

All the `\n` bits make sure there’s a linebreak instead of it all running on, and the `+` symbols connect the individual instructions into one big transformation that happens at once.

Put the name of the template you’re using where the example says `TePapaColl`.

For each template field you want to populate, include a section that looks like this:

```
if(isBlank(cells.qualifiedName.value), "", "|qualifiedName=" + cells.qualifiedName.value + "\n") +
```

Here, each field checks if the record has data for it. If not, it knows to leave it out, but if there is data, it’ll pull it into the right part of the Wikitext column. `qualifiedName` is the label for both the column in the OpenRefine project and the field in the template.

For each category you want to add to all your images, include a section like this:

```
[[Category:Botany in Te Papa Tongarewa]]\n" +
```

But if there are categories you only want to include on some records, do this instead:

```
if(isBlank(cells.CategoryScientificName.value), "", "[[Category:" + cells.CategoryScientificName.value + "]]\n") +
```

Like the field data, this only adds the category to the Wikitext if you’ve got a value to fill it in.

## Full GREL instruction used by Te Papa with TePapaColl template
```
"== {{int:filedesc}} ==\n" +
"{{TePapaColl\n" +
if(isBlank(cells.title.value), "", "|title=" + cells.title.value + "\n") +
if(isBlank(cells.description.value), "", "|description=" + cells.description.value + "\n") +
if(isBlank(cells.mātaurangaMāori.value), "", "|MātaurangaMāori=" + cells.MātaurangaMāori.value + "\n") +
if(isBlank(cells.creator.value), "", "|creator=" + cells.creator.value + "\n") +
if(isBlank(cells.dateCreated.value), "", "|dateCreated=" + cells.dateCreated.value + "\n") +
if(isBlank(cells.placeCreated.value), "", "|placeCreated=" + cells.placeCreated.value + "\n") +
if(isBlank(cells.madeOf.value), "", "|madeOf=" + cells.madeOf.value + "\n") +
if(isBlank(cells.depicts.value), "", "|depicts=" + cells.depicts.value + "\n") +
if(isBlank(cells.basisOfRecord.value), "", "|basisOfRecord=" + cells.basisOfRecord.value + "\n") +
if(isBlank(cells.vernacularName.value), "", "|vernacularName=" + cells.vernacularName.value + "\n") +
if(isBlank(cells.qualifiedName.value), "", "|QualifiedName=" + cells.QualifiedName.value + "\n") +
if(isBlank(cells.typeStatus.value), "", "|typeStatus=" + cells.typeStatus.value + "\n") +
if(isBlank(cells.identifiedBy.value), "", "|identifiedBy=" + cells.identifiedBy.value + "\n") +
if(isBlank(cells.genusVernacularName.value), "", "|genusVernacularName=" + cells.genusVernacularName.value + "\n") +
if(isBlank(cells.family.value), "", "|family=" + cells.family.value + "\n") +
if(isBlank(cells.dateCollected.value), "", "|dateCollected=" + cells.dateCollected.value + "\n") +
if(isBlank(cells.recordedBy.value), "", "|recordedBy=" + cells.recordedBy.value + "\n") +
if(isBlank(cells.country.value), "", "|country=" + cells.country.value + "\n") +
if(isBlank(cells.stateProvince.value), "", "|stateProvince=" + cells.stateProvince.value + "\n") +
if(isBlank(cells.catalogueRestrictions.value), if(isBlank(cells.preciseLocality.value), "", "|preciseLocality=" + cells.preciseLocality.value + "\n"), "") +
if(isBlank(cells.elevation.value), "", "|elevation=" + cells.elevation.value + "\n") +
if(isBlank(cells.depth.value), "", "|depth=" + cells.depth.value + "\n") +
if(isBlank(cells.institutionCode.value), "", "|institutionCode=" + cells.institutionCode.value + "\n") +
if(isBlank(cells.institution.value), "", "|institution=" + cells.institution.value + "\n") +
if(isBlank(cells.identifier.value), "", "|identifier=" + cells.identifier.value + "\n") +
if(isBlank(cells.references.value), "", "|references=" + cells.references.value + "\n") +
if(isBlank(cells.creditLine.value), "", "|creditLine=" + cells.creditLine.value + "\n") +
"}}\n" +
"=={{int:license-header}}==\n" +
"{{cc-by-4.0}}\n" +
"[[Category:Botany in Te Papa Tongarewa]]\n" +
"[[Category:Uploaded by Te Papa staff]]\n" +
"[[Category:Herbarium specimens]]\n" +
if(isBlank(cells.categoryScientificName.value), "", "[[Category:" + cells.categoryScientificName.value + "]]\n") +
if(isBlank(cells.typeStatus.value), "", "[[Category:Museum of New Zealand Te Papa Tongarewa type specimens]]\n")
```
