var loadClusterInstances = function (group_name) {
    console.log("Loadig data for " + group_name)
    $("#cluster-instances-" + group_name).load("/ajax-cluster-instances", { "group_name": group_name }, function () {
        setTimeout(loadClusterInstances, 15000, group_name);
    });
}

var elbStats = new Array();

var loadElbStats = function (elb_name) {

    $.ajax({
        url: "/ajax-elb-stats",
        type: 'POST',
        cache: false,
        dataType: "json",
        data: {'elb_name': elb_name},
        success: function (result) {
            $("#loader-" + elb_name).remove();
            if (result.length > 0) {
                var graph = null;
                if (elb_name in elbStats) {
                    graph = elbStats[elb_name];
                    graph.setData(result);
                    elbStats[elb_name] = graph;
                }
                else {
                    graph = Morris.Area({
                        element: "elb-stats-" + elb_name,
                        data: result,
                        xkey: 'Timestamp',
                        ykeys: ['Sum'],
                        labels: ['Requests'],
                        pointSize: 2,
                        hideHover: 'auto',
                        resize: true
                    });
                    elbStats[elb_name] = graph;
                }
            }
            else {
                $("#elb-stats" + elb_name).html('<div class="alert alert-warning" role="alert">No data available</div>');
            }
            setTimeout(loadElbStats, 30000, elb_name);
        }
    })


}

var cpuStats = Array();

var loadCpuStats = function (group_name) {

    $.ajax({
        url: "/ajax-cpu-stats",
        type: 'POST',
        cache: false,
        dataType: "json",
        data: {'group_name': group_name},
        success: function (result) {
            $("#loader-" + group_name).remove();
            if (result.length > 0) {
                var graph = null;
                if (group_name in cpuStats) {
                    graph = cpuStats[group_name];
                    graph.setData(result);
                    cpuStats[group_name] = graph;
                }
                else {
                    var graph = Morris.Area({
                        element: "cpu-stats-" + group_name,
                        data: result,
                        xkey: 'Timestamp',
                        ykeys: ['Average'],
                        labels: ['CPU %'],
                        pointSize: 2,
                        hideHover: 'auto',
                        resize: true
                    });
                    cpuStats[group_name] = graph;
                }
            }


        }


    })

    setTimeout(loadCpuStats, 30000, group_name);


}


var showEditDialog = function (groupName) {

    BootstrapDialog.show({
        title: '',
        message: "Capacity: <form id='editform'><input type='hidden' name='group_name' value='" + groupName + "'/><input type='text' name='capacity' /> </form>",
        buttons: [
            {
                icon: 'glyphicon glyphicon-send',
                label: 'Edit Cluster',
                cssClass: 'btn-primary',
                autospin: true,
                action: function (dialogRef) {
                    dialogRef.enableButtons(false);
                    dialogRef.setClosable(false);

                    $.ajax({
                        type: "POST",
                        url: "/edit-cluster",
                        data: $('#editform').serialize(),
                        cache: false,
                        success: function (result) {
                            dialogRef.close();
                            BootstrapDialog.alert({
                                message: result,
                                type: BootstrapDialog.TYPE_SUCCESS
                            });
                            loadClusterInstances(groupName);
                        },
                        error: function (result) {
                            dialogRef.close();
                            BootstrapDialog.alert({
                                message: result.responseText,
                                type: BootstrapDialog.TYPE_DANGER
                            });
                        }
                    });
                }
            },
            {
                label: 'Close',
                action: function (dialogRef) {
                    dialogRef.close();
                }
            }
        ]
    });
}


var showLaunchDialog = function (imageId) {

    BootstrapDialog.show({
        title: '',
        message: $('<div></div>').load('/launch-form', {'image-id': imageId}),
        buttons: [
            {
                icon: 'glyphicon glyphicon-send',
                label: 'Launch Cluster',
                cssClass: 'btn-primary',
                autospin: true,
                action: function (dialogRef) {
                    dialogRef.enableButtons(false);
                    dialogRef.setClosable(false);

                    $.ajax({
                        type: "POST",
                        url: "/launch-cluster",
                        data: $('#launchform').serialize(),
                        cache: false,
                        success: function (result) {
                            dialogRef.close();
                            BootstrapDialog.alert({
                                message: result,
                                type: BootstrapDialog.TYPE_SUCCESS
                            });
                            loadInstances();
                        },
                        error: function (result) {
                            dialogRef.close();
                            BootstrapDialog.alert({
                                message: result.responseText,
                                type: BootstrapDialog.TYPE_DANGER
                            });
                        }
                    });
                }
            },
            {
                label: 'Close',
                action: function (dialogRef) {
                    dialogRef.close();
                }
            }
        ]
    });
}

var showImageDialog = function (instanceId) {

    BootstrapDialog.show({
        title: '',
        message: "Description: <form id='imageform'><input type='hidden' name='id' value='" + instanceId + "'/><input type='text' name='description' /> </form>",
        buttons: [
            {
                icon: 'glyphicon glyphicon-send',
                label: 'Create Image',
                cssClass: 'btn-primary',
                autospin: true,
                action: function (dialogRef) {
                    dialogRef.enableButtons(false);
                    dialogRef.setClosable(false);

                    $.ajax({
                        type: "POST",
                        url: "/create-image",
                        data: $('#imageform').serialize(),
                        cache: false,
                        success: function (result) {
                            dialogRef.close();
                            BootstrapDialog.alert({
                                message: result,
                                type: BootstrapDialog.TYPE_SUCCESS
                            });
                            loadImages();
                        },
                        error: function (result) {
                            dialogRef.close();
                            BootstrapDialog.alert({
                                message: result.responseText,
                                type: BootstrapDialog.TYPE_DANGER
                            });
                        }
                    });
                }
            },
            {
                label: 'Close',
                action: function (dialogRef) {
                    dialogRef.close();
                }
            }
        ]
    });

}

var loadImages = function () {

    $("#images").load("/ajax-image-list", function () {
        //setTimeout(loadClusterInstances(), 5000);
    });
}

var loadInstances = function () {

    $("#instances").load("/ajax-master-instances", function () {
        //setTimeout(loadClusterInstances(), 5000);
    });
}

var showDeleteDialog = function (stackId) {

    BootstrapDialog.show({
        title: '',
        message: "Do you really want to delete this cluster?",
        buttons: [
            {
                icon: 'glyphicon glyphicon-send',
                label: 'Delete Cluster',
                cssClass: 'btn-primary',
                autospin: true,
                action: function (dialogRef) {
                    dialogRef.enableButtons(false);
                    dialogRef.setClosable(false);

                    $.ajax({
                        type: "POST",
                        url: "/delete-cluster",
                        data: {'stack-id': stackId},
                        cache: false,
                        success: function (result) {
                            dialogRef.close();
                            BootstrapDialog.alert({
                                message: result,
                                type: BootstrapDialog.TYPE_SUCCESS
                            });
                            loadPage();
                        },
                        error: function (result) {
                            dialogRef.close();
                            BootstrapDialog.alert({
                                message: result.responseText,
                                type: BootstrapDialog.TYPE_DANGER
                            });
                        }
                    });
                }
            },
            {
                label: 'Close',
                action: function (dialogRef) {
                    dialogRef.close();
                }
            }
        ]
    });

}