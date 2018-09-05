<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="15008000">
	<Item Name="My Computer" Type="My Computer">
		<Property Name="server.app.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.control.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="server.tcp.port" Type="Int">0</Property>
		<Property Name="server.tcp.serviceName" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.tcp.serviceName.default" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.vi.callsEnabled" Type="Bool">true</Property>
		<Property Name="server.vi.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>
		<Item Name="getDeviceCount.vi" Type="VI" URL="../getDeviceCount.vi"/>
		<Item Name="getDeviceParam.vi" Type="VI" URL="../getDeviceParam.vi"/>
		<Item Name="getFGenDevices.vi" Type="VI" URL="../getFGenDevices.vi"/>
		<Item Name="Dependencies" Type="Dependencies">
			<Item Name="instr.lib" Type="Folder">
				<Item Name="niModInst Close Installed Devices Session.vi" Type="VI" URL="/&lt;instrlib&gt;/niModInst/niModInst Close Installed Devices Session.vi"/>
				<Item Name="niModInst Get Installed Device Attribute (I32).vi" Type="VI" URL="/&lt;instrlib&gt;/niModInst/niModInst Get Installed Device Attribute (I32).vi"/>
				<Item Name="niModInst Get Installed Device Attribute (poly).vi" Type="VI" URL="/&lt;instrlib&gt;/niModInst/niModInst Get Installed Device Attribute (poly).vi"/>
				<Item Name="niModInst Get Installed Device Attribute (String).vi" Type="VI" URL="/&lt;instrlib&gt;/niModInst/niModInst Get Installed Device Attribute (String).vi"/>
				<Item Name="niModInst Open Installed Devices Session.vi" Type="VI" URL="/&lt;instrlib&gt;/niModInst/niModInst Open Installed Devices Session.vi"/>
				<Item Name="niModInst Set Error.vi" Type="VI" URL="/&lt;instrlib&gt;/niModInst/niModInst Set Error.vi"/>
			</Item>
			<Item Name="vi.lib" Type="Folder">
				<Item Name="Error Cluster From Error Code.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Error Cluster From Error Code.vi"/>
			</Item>
			<Item Name="niModInst_64.dll" Type="Document" URL="niModInst_64.dll">
				<Property Name="NI.PreserveRelativePath" Type="Bool">true</Property>
			</Item>
		</Item>
		<Item Name="Build Specifications" Type="Build">
			<Item Name="DataStation_Labview" Type="DLL">
				<Property Name="App_copyErrors" Type="Bool">true</Property>
				<Property Name="App_INI_aliasGUID" Type="Str">{ACF9624E-AE9D-4C1A-B746-31B6F90741EE}</Property>
				<Property Name="App_INI_GUID" Type="Str">{3A29B96A-E4CB-4F3E-836F-18967228F140}</Property>
				<Property Name="App_serverConfig.httpPort" Type="Int">8002</Property>
				<Property Name="Bld_autoIncrement" Type="Bool">true</Property>
				<Property Name="Bld_buildCacheID" Type="Str">{3C6230CB-6B13-4E1F-BFE5-A5FE52CB1E3C}</Property>
				<Property Name="Bld_buildSpecName" Type="Str">DataStation_Labview</Property>
				<Property Name="Bld_excludeInlineSubVIs" Type="Bool">true</Property>
				<Property Name="Bld_excludeLibraryItems" Type="Bool">true</Property>
				<Property Name="Bld_excludePolymorphicVIs" Type="Bool">true</Property>
				<Property Name="Bld_localDestDir" Type="Path">../inc</Property>
				<Property Name="Bld_localDestDirType" Type="Str">relativeToCommon</Property>
				<Property Name="Bld_modifyLibraryFile" Type="Bool">true</Property>
				<Property Name="Bld_previewCacheID" Type="Str">{669EDF20-E4B0-4B8E-915B-9F3F7CC9A1DA}</Property>
				<Property Name="Bld_version.build" Type="Int">20</Property>
				<Property Name="Bld_version.major" Type="Int">1</Property>
				<Property Name="Destination[0].destName" Type="Str">DataStation_Labview.dll</Property>
				<Property Name="Destination[0].path" Type="Path">../inc/DataStation_Labview.dll</Property>
				<Property Name="Destination[0].preserveHierarchy" Type="Bool">true</Property>
				<Property Name="Destination[0].type" Type="Str">App</Property>
				<Property Name="Destination[1].destName" Type="Str">Support Directory</Property>
				<Property Name="Destination[1].path" Type="Path">../inc/data</Property>
				<Property Name="DestinationCount" Type="Int">2</Property>
				<Property Name="Dll_compatibilityWith2011" Type="Bool">false</Property>
				<Property Name="Dll_delayOSMsg" Type="Bool">true</Property>
				<Property Name="Dll_headerGUID" Type="Str">{6561D9D2-37FD-420F-A5D0-D30AFF191CD0}</Property>
				<Property Name="Dll_includeTypeLibrary" Type="Bool">true</Property>
				<Property Name="Dll_libGUID" Type="Str">{9C4FE9E5-A729-4DC9-B93E-D7EF9886E1E3}</Property>
				<Property Name="Source[0].itemID" Type="Str">{07746664-F5A0-4A83-BD1F-551288FE241D}</Property>
				<Property Name="Source[0].type" Type="Str">Container</Property>
				<Property Name="Source[1].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[1].itemID" Type="Ref">/My Computer/getDeviceCount.vi</Property>
				<Property Name="Source[1].sourceInclusion" Type="Str">TopLevel</Property>
				<Property Name="Source[1].type" Type="Str">ExportedVI</Property>
				<Property Name="Source[2].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[2].itemID" Type="Ref">/My Computer/getDeviceParam.vi</Property>
				<Property Name="Source[2].sourceInclusion" Type="Str">TopLevel</Property>
				<Property Name="Source[2].type" Type="Str">ExportedVI</Property>
				<Property Name="Source[3].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[3].itemID" Type="Ref">/My Computer/getFGenDevices.vi</Property>
				<Property Name="Source[3].sourceInclusion" Type="Str">TopLevel</Property>
				<Property Name="Source[3].type" Type="Str">ExportedVI</Property>
				<Property Name="SourceCount" Type="Int">4</Property>
				<Property Name="TgtF_companyName" Type="Str">Baylor University</Property>
				<Property Name="TgtF_fileDescription" Type="Str">DataStation_Labview</Property>
				<Property Name="TgtF_internalName" Type="Str">DataStation_Labview</Property>
				<Property Name="TgtF_legalCopyright" Type="Str">Copyright © 2018 Baylor University</Property>
				<Property Name="TgtF_productName" Type="Str">DataStation_Labview</Property>
				<Property Name="TgtF_targetfileGUID" Type="Str">{5F8A5B82-8886-404A-9E8D-913BC85DDA08}</Property>
				<Property Name="TgtF_targetfileName" Type="Str">DataStation_Labview.dll</Property>
			</Item>
		</Item>
	</Item>
</Project>
