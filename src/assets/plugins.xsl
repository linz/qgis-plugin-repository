<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/plugins">

<html>
<head>
<title>Qgis Plugins</title>
<!--link href="xsl.css" rel="stylesheet" type="text/css" /-->

<style>
body  { 
   font-family:Verdana, Arial, Helvetica, sans-serif;
width: 50em;
 }

div.plugin { 
 background-color:#E6F2FF;
 border:1px solid #BFDFFF;
 clear:both;
 display:block;
 padding:0 0 0.5em;
 margin:1em;
}

div.head { 
  background-color:#BFDFFF;
  border-bottom-width:0;
  display:block;
  font-size:110%;
  font-weight:bold;
  margin:0;
  padding:0.3em 1em;
}

div.description{ 
  display: block;
  float:none;
  margin:0;
  text-align: left;
  padding:0.2em 0.5em 0.4em;
  color: black;
  font-size:100%;
  font-weight:normal;
 }

div.download, div.author{ 
  font-size: 80%;
  padding: 0em 0em 0em 1em;
 }
</style>

</head>
<body>
<h1>Qgis plugins</h1>
<xsl:for-each select="/plugins/pyqgis_plugin">
<div class="plugin">
<div class="head">
	<xsl:choose>
		<xsl:when test="homepage != ''">
<xsl:element name="a">
<xsl:attribute name="href">
<xsl:value-of select="homepage" />
</xsl:attribute>
<xsl:value-of select="@name" /> : <xsl:value-of select="@version" />
</xsl:element>
		</xsl:when>
	<xsl:otherwise>
<xsl:value-of select="@name" /> : <xsl:value-of select="@version" />
	</xsl:otherwise>
	</xsl:choose>
</div>
<div class="description">
<xsl:value-of select="description" />
</div>
<div class="download">
Download:
<xsl:element name="a">
 <xsl:attribute name="href">
  <xsl:value-of select="download_url" />
 </xsl:attribute>
 <xsl:value-of select="file_name" />
</xsl:element>
</div>
<div class="author">
Author: <xsl:value-of select="author_name" />
</div>
</div>
</xsl:for-each>


</body>
</html>

</xsl:template>

</xsl:stylesheet>
