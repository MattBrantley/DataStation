#include "extcode.h"
#ifdef __cplusplus
extern "C" {
#endif
typedef struct {
	LStrHandle Name;
	LStrHandle Model;
	LStrHandle SerialNumber;
} Cluster;
typedef struct {
	int32_t dimSize;
	Cluster elt[1];
} ClusterArrayBase;
typedef ClusterArrayBase **ClusterArray;

/*!
 * GetDeviceCount
 */
int32_t __cdecl GetDeviceCount(char driver[]);
/*!
 * GetDeviceParam
 */
void __cdecl GetDeviceParam(char driver[], char param[], int32_t deviceNo, 
	char Result[], int32_t len);
/*!
 * GetFGenDevices
 */
void __cdecl GetFGenDevices(ClusterArray *Array);

MgErr __cdecl LVDLLStatus(char *errStr, int errStrLen, void *module);

/*
* Memory Allocation/Resize/Deallocation APIs for type 'ClusterArray'
*/
ClusterArray __cdecl AllocateClusterArray (int32 elmtCount);
MgErr __cdecl ResizeClusterArray (ClusterArray *hdlPtr, int32 elmtCount);
MgErr __cdecl DeAllocateClusterArray (ClusterArray *hdlPtr);

#ifdef __cplusplus
} // extern "C"
#endif

