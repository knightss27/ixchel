<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xsl:stylesheet [
	<!ENTITY nbsp "&#160;">
	<!ENTITY deg "&#176;">
	<!ENTITY amin "&#180;">
	<!ENTITY asec "&#168;">
        <!ENTITY Beta "&#946;">
        <!ENTITY chi "&#967;">
        <!ENTITY darr "&#8595;">
	]>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<!-- 
#				stiff.xsl
#
# Global XSL template
#
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
#	This file part of:	STIFF
#
#	Copyright:		(C) 2003-2010 Emmanuel Bertin - IAP/CNRS/UPMC
#
#	License:		GNU General Public License
#
#	STIFF is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
# 	(at your option) any later version.
#	STIFF is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	You should have received a copy of the GNU General Public License
#	along with STIFF. If not, see <http://www.gnu.org/licenses/>.
#
#	Last modified:		13/10/2010
#
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% -->

 <xsl:template match="/">
  <xsl:variable name="date" select="/VOTABLE/RESOURCE/RESOURCE[@name='MetaData']/PARAM[@name='Date']/@value"/>
  <xsl:variable name="time" select="/VOTABLE/RESOURCE/RESOURCE[@name='MetaData']/PARAM[@name='Time']/@value"/>
  <HTML>
   <HEAD>
    <link rel="shortcut icon" type="image/x-icon" href="http://astromatic.net/xsl/favicon.ico" />
    <script type="text/javascript" src="http://astromatic.net/xsl/sorttable.js"/>

    <style type="text/css">
     p {
      font-family: sans-serif;
      }
     p.italic {font-style: italic}
     body {
      margin: 10px;
      background-color: #e0e0e0;
      background-image: url("http://astromatic.net/xsl/body_bg.jpg");
      background-repeat: repeat-x;
      background-position: top;
      min-width:662px;
      }
     mono {font-family: monospace}
     elmin {color: green }
     elmax {color: red }
     el {
      font-family: monospace;
      font-size: 100%;
      color: black;
      }
     elm {
      font-family: monospace;
      font-size: 67%;
      white-space: nowrap;
      }
     a {text-decoration: none; font-style: bold; color: #476674}
     a:hover {text-decoration: underline;}
     #header {
      padding: 5px;
      min-width: 662px;
      background-image: url("http://astromatic.net/xsl/astromaticleft.png");
      background-repeat: repeat-x;
      background-position: left top;
      text-align: left;
      font-size: 1.2em;
      margin: 0 0 30px 0;
      color:#d3e7f0;
      font-weight: bold;
      }
     th {
      background-color:#d3e7f0;
      border-top: 1px solid white;
      border-left: 1px solid white;
      border-right: 1px solid #476674;
      border-bottom: 1px solid #476674;
      -moz-border-radius: 3px;
      -khtml-border-radius: 3px;
      -webkit-border-radius: 3px;
      border-radius: 3px;
      padding: 2px;
      line-height: 12px;
      }
     td {
      background-color:#f2f4f4;
      padding-left: 2px;
      padding-right: 2px;
      }
     table.sortable {
      border-top: 1px solid #476674;
      border-left: 1px solid #476674;
      border-right: 1px solid white;
      border-bottom: 1px solid white;
      -moz-border-radius: 3px;
      -khtml-border-radius: 3px;
      -webkit-border-radius: 3px;
      border-radius: 3px;
      }
     table.sortable a.sortheader {
      background-color:#d3e7f0;
      font-weight: bold;
      font-size: 80%;
      text-decoration: none;
      display: button;
      }

     table.sortable span.sortarrow {
      color: black;
      font-weight: bold;
      text-decoration: blink;
      }
     table.sortable a.sortheader.sub {vertical-align: sub}
     </style>

     <title>
      Processing summary on <xsl:value-of select="$date"/> at <xsl:value-of select="$time"/>
     </title>
    </HEAD>
    <BODY>
     <div id="header">
      <a href="http://astromatic.net"><img style="vertical-align: middle; border:0px" src="http://astromatic.net/xsl/astromatic.png" title="Astromatic home" alt="Astromatic.net" /></a>  Processing summary
     </div>
    <xsl:call-template name="VOTable"/>
   </BODY>
  </HTML>
 </xsl:template>

<!-- **************** Generic XSL template for VOTables ****************** -->
 <xsl:template name="VOTable">
  <xsl:for-each select="/VOTABLE">
   <xsl:call-template name="Resource"/>
  </xsl:for-each>
 </xsl:template>

<!-- *************** Generic XSL template for Resources ****************** -->
 <xsl:template name="Resource">
  <xsl:for-each select="RESOURCE">
   <xsl:choose>
    <xsl:when test="@ID='STIFF'">
     <xsl:call-template name="STIFF"/>
    </xsl:when>
   </xsl:choose>
  </xsl:for-each>
 </xsl:template>

<!-- ********************** XSL template for STIFF *********************** -->
 <xsl:template name="STIFF">
  <xsl:for-each select="RESOURCE[@ID='MetaData']">
   <xsl:call-template name="RunInfo"/>
   <xsl:for-each select="TABLE[@ID='Input_Image_Data']">
    <xsl:call-template name="Input_Image_Data"/>
   </xsl:for-each>
   <xsl:for-each select="RESOURCE[@ID='Config']">
    <xsl:call-template name="Config"/>
   </xsl:for-each>
   <xsl:for-each select="TABLE[@ID='Warnings']">
    <xsl:call-template name="Warnings"/>
   </xsl:for-each>
  </xsl:for-each>
 </xsl:template>

<!-- ************* Generic XSL RunInfo template for MetaData ************* -->
 <xsl:template name="RunInfo">
  <p>
<!-- Software name, version, date, time and number of threads -->
   <a>
    <xsl:attribute name="href">
     <xsl:value-of select="PARAM[@name='Soft_URL']/@value"/>
    </xsl:attribute>
    <b>
     <xsl:value-of select="PARAM[@name='Software']/@value"/>&nbsp;<xsl:value-of select="PARAM[@name='Version']/@value"/>
    </b>
   </a>
   started on
   <b><xsl:value-of select="PARAM[@name='Date']/@value"/></b>
   at
   <b><xsl:value-of select="PARAM[@name='Time']/@value"/></b>
   with
   <b><xsl:value-of select="PARAM[@name='NThreads']/@value"/></b>
   thread<xsl:if test="PARAM[@name='NThreads']/@value &gt; 1">s</xsl:if>

<!-- Run time -->
   <xsl:variable name="duration" select="PARAM[@name='Duration']/@value"/>
   (run time:
    <b>
     <xsl:choose> 
      <xsl:when test="$duration &gt; 3600.0">
       <xsl:value-of
	select='concat(string(floor($duration div 3600)),
	" h ", format-number(floor(($duration div 60) mod 60.0), "00"),
	" min")'/>
      </xsl:when>
      <xsl:otherwise>
       <xsl:choose>
        <xsl:when test="$duration &gt; 60.0">
         <xsl:value-of
	  select='concat(format-number(floor($duration div 60),"##"),
	  " min ", format-number(floor($duration mod 60.0), "00")," s")'/>
        </xsl:when>
        <xsl:otherwise>
         <xsl:value-of select='concat(string($duration), " s")'/>
        </xsl:otherwise>
       </xsl:choose>
      </xsl:otherwise>
     </xsl:choose>
    </b>)
    <br />
   by user <b><xsl:value-of select="PARAM[@name='User']/@value"/></b>
   from <b><xsl:value-of select="PARAM[@name='Host']/@value"/></b>
   in <b><mono><xsl:value-of select="PARAM[@name='Path']/@value"/></mono></b>
  </p>
  <p>
   <b style="color: red"><xsl:if test="PARAM[@name='Error_Msg']/@value &gt; 0">
    An Error occured!!! </xsl:if>
   <xsl:value-of select="PARAM[@name='Error_Msg']/@value"/></b>
  </p>
 </xsl:template>

<!-- ****************** XSL template for Input_Image_Data **************** -->
  <xsl:template name="Input_Image_Data">
   <xsl:variable name="name" select="count(FIELD[@name='Image_Name']/preceding-sibling::FIELD)+1"/>
   <xsl:variable name="ident" select="count(FIELD[@name='Image_Ident']/preceding-sibling::FIELD)+1"/>
   <xsl:variable name="size" select="count(FIELD[@name='Image_Size']/preceding-sibling::FIELD)+1"/>
   <xsl:variable name="back" select="count(FIELD[@name='Level_Background']/preceding-sibling::FIELD)+1"/>
   <xsl:variable name="min" select="count(FIELD[@name='Level_Min']/preceding-sibling::FIELD)+1"/>
   <xsl:variable name="max" select="count(FIELD[@name='Level_Max']/preceding-sibling::FIELD)+1"/>
   <p>
    <BUTTON type="button" onclick="showhideTable('imdata')" title="click to expand">
     Input image data&nbsp;&darr;
    </BUTTON>
    <TABLE class="sortable" id="imdata" BORDER="2" style="display: none">
     <TR>
      <TH>Filename</TH>
      <TH>Identifier</TH>
      <TH>Size</TH>
      <TH>Background level (ADU)</TH>
      <TH>Minimum level (ADU)</TH>
      <TH>Maximum level (ADU)</TH>
     </TR>
     <xsl:for-each select="DATA/TABLEDATA">
      <xsl:for-each select="TR">
       <tr>
<!-- Catalog name -->
        <td>
         <el><xsl:value-of select="TD[$name]"/></el>
        </td>
<!-- Identifier -->
        <td align="center">
         <el><xsl:value-of select="TD[$ident]"/></el>
        </td>
<!-- Image size -->
        <td align="center">
         <el><xsl:value-of select="TD[$size]"/></el>
        </td>
<!-- Background level -->
        <td align="center">
         <el><xsl:value-of select="TD[$back]"/></el>
        </td>
<!-- Minimum level -->
        <td align="center">
         <el><xsl:value-of select="TD[$min]"/></el>
        </td>
<!-- Maximum level -->
        <td align="center">
         <el><xsl:value-of select="TD[$max]"/></el>
        </td>
       </tr>
      </xsl:for-each>
     </xsl:for-each>
    </TABLE>
   </p>
 </xsl:template>

<!-- ********************** XSL template for Config File ********************** -->
  <xsl:template name="Config">
   <p>
    <BUTTON type="button" onclick="showhideTable('config')" title="click to expand">
     Configuration File: <B><xsl:value-of select="PARAM[@name='Prefs_Name']/@value"/></B>&nbsp;&darr;
    </BUTTON>
    <TABLE id="config" class="sortable" style="display: none">
     <TR>
      <TH>Config Parameter</TH>
      <TH>Value</TH>
     </TR>
     <xsl:for-each select="PARAM[position()>2]">
      <tr>
       <td><el><xsl:value-of select="@name"/></el></td>
       <td><el><xsl:value-of select="@value"/></el></td>
      </tr>
     </xsl:for-each>
    </TABLE>
   </p>
   <p>
    <BUTTON type="button" onclick="showhideTable('commandline')" title="click to expand">
     Command Line&nbsp;&darr;
    </BUTTON>
    <TABLE id="commandline" style="display: none">
     <TR>
      <TD style="font-size: 80%;"><el><xsl:value-of select="PARAM[@name='Command_Line']/@value"/></el></TD>
     </TR>
    </TABLE>
   </p>
  </xsl:template>

<!-- ********************** XSL template for Warnings ********************** -->
  <xsl:template name="Warnings">
   <xsl:variable name="date" select="count(FIELD[@name='Date']/preceding-sibling::FIELD)+1"/>
   <xsl:variable name="time" select="count(FIELD[@name='Time']/preceding-sibling::FIELD)+1"/>
   <xsl:variable name="msg" select="count(FIELD[@name='Msg']/preceding-sibling::FIELD)+1"/>
   <p>
    <BUTTON type="button" onclick="showhideTable('warnings')" title="click to expand">
     Warnings (limited to the last 1000)&nbsp;&darr;
    </BUTTON>
    <TABLE id="warnings" class="sortable" style="display: none">
     <TR style="font-size: 80%;">
      <TH>Date</TH>
      <TH>Time</TH>
      <TH>Message</TH>
     </TR>
     <xsl:for-each select="DATA/TABLEDATA">
      <xsl:for-each select="TR">
       <tr>
        <td >
         <el><xsl:value-of select="TD[$date]"/></el>
        </td>
        <td>
         <el><xsl:value-of select="TD[$time]"/></el>
        </td>
        <td align="center">
         <el><xsl:value-of select="TD[$msg]"/></el>
        </td>
       </tr>
      </xsl:for-each>
     </xsl:for-each>
    </TABLE>
   </p>
 </xsl:template>

 <xsl:template name="Rest">
</xsl:template>
</xsl:stylesheet>

