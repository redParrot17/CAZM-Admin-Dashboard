
// Primary courses elements
let $coursesTable = $('#table');
let $resyncCoursesBtn = $('#resync');
let $createCourseBtn = $('#create');
let $editCourseBtn = $('#change');
let $deleteCoursesBtn = $('#remove');

// Secondary edit course elements
let $editRequisitesTable = $('#editCourseRequisiteTable');
let $editCourseCode = $('#editCourseCode');
let $editCourseName = $('#editCourseName');
let $editCourseTerm = $('#editCourseTerm');
let $editCourseCredits = $('#editCourseCredits');
let $editCourseSave = $('#editCourseSave');
let $editCourseModal = $('#editModal');

let $editCourseRequisiteGroup = $('#editCourseRequisiteGroupNum');
let $editCourseRequisiteType = $('#editCourseRequisiteType');
let $editCourseRequisiteCode = $('#editCourseRequisiteCode');
let $editCourseRequisiteAdd = $('#editCourseRequisiteAdd');

// Secondary create course elements
let $createRequisitesTable = $('#createCourseRequisiteTable');
let $createCourseCode = $('#newCourseCode');
let $createCourseName = $('#newCourseName');
let $createCourseTerm = $('#newCourseTerm');
let $createCourseCredits = $('#newCourseCredits');
let $createCourseSave = $('#createCourseSave');
let $createCourseModal = $('#createModal');

let $createCourseRequisiteGroup = $('#newCourseRequisiteGroupNum');
let $createCourseRequisiteType = $('#newCourseRequisiteType');
let $createCourseRequisiteCode = $('#newCourseRequisiteCode');
let $createCourseRequisiteAdd = $('#newCourseRequisiteAdd');

// General
let uid = 0;
let requisites = [];
let isSyncing = false;
let data = [];

// Tracking edited courses
let oldTerm = null;


function setSyncing(value) {
    isSyncing = value === 'true';
}

function setData(d) {
    data = d;
    let id = 0;
    data.forEach(function(element) {
        element.id = id++;
    })
    $coursesTable.bootstrapTable('load', data);
}


// Requisites //

function resetReqisites() {
    requisites = [];
    uid = 0;
}

function addRequisite(group, type, code) {
    uid++;
    let requisite = {
        id: uid,
        group: group,
        type: type,
        code: code
    };
    requisites.push(requisite);
    return requisite;
}

function removeRequisite(id) {
    requisites = requisites.filter(obj => obj.id !== id);
}

function initRowRequisites(row) {
    resetReqisites();
    let rowNum = 0;
    Object.entries(row.requisites).forEach(requisiteGroup => {
        rowNum += 1;
        requisiteGroup[1].forEach(requisite => {
            addRequisite(rowNum, requisite[0], requisite[1]);
        });
    });
}

function exportRequisites() {
    let container = {};
    requisites.forEach(requisite => {
        let id = requisite.group;
        if (id in container) {
            container[id].push([requisite.type, requisite.code])
        } else {
            container[id] = [[requisite.type, requisite.code]]
        }
    });
    let returnValue = [];
    Object.entries(container).forEach(group => {
        returnValue.push(group[1]);
    });
    return returnValue;
}


// Sends an html POST request to the current location
function httpPost(object) {
    let xhr = new XMLHttpRequest();
    let url = window.location.href;
    xhr.open("POST", url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify(object));
}

// Gets the currently selected row
function getSelectedRow() {
    let selections = $coursesTable.bootstrapTable('getSelections');
    if (selections.length) return selections[0];
}

// Requisite deletion event handler
window.operateEvents = {
    'click .remove': function(e, value, row, index) {
        $createRequisitesTable.bootstrapTable('remove', {
            field: 'id',
            values: [row.id]
        });
        $editRequisitesTable.bootstrapTable('remove', {
            field: 'id',
            values: [row.id]
        });
        requisites = requisites.filter(obj => obj.id !== row.id)
    }
}

// Adds the deletion icon to the tables with individual row deletion
function operateFormatter(value, row, index) {
    return [
        '<a class="remove" href="javascript:void(0)" title="Remove">',
        '<i class="fa fa-trash"></i>',
        '</a>'
    ].join('')
}


// Initialize once document has finished loading
$(document).ready(function() {

    // Toggle visibility of sidebar on click
    $('#sidebarCollapse').on('click', function() {
        $('#sidebar').toggleClass('active');
        $(this).toggleClass('active');
    });

    $coursesTable.bootstrapTable('load', data);

    // Toggle enabled state of delete button on selection
    $coursesTable.on('check.bs.table uncheck.bs.table check-all.bs.table uncheck-all.bs.table', function() {
        let selections = $coursesTable.bootstrapTable('getSelections');
        
        // edit button should only be clickable when only one thing is selected
        $editCourseBtn.prop('disabled', selections.length !== 1);

        // delete button should only be clickable when at least one thing is selected
        $deleteCoursesBtn.prop('disabled', selections.length === 0);
    });

    // Structure of the requisite tables
    let requisiteTableStructure = {
        data: [],
        columns: [
            {field: 'group', title: 'Group'},
            {field: 'type', title: 'Type'},
            {field: 'code', title: 'Code'},
            {
                field: 'operate',
                title: 'Del',
                align: 'center',
                clickToSelect: false,
                events: window.operateEvents,
                formatter: operateFormatter
            }
        ]
    };

    // Initialize create and edit requisites tables
    $createRequisitesTable.bootstrapTable('destroy').bootstrapTable(requisiteTableStructure);
    $editRequisitesTable.bootstrapTable('destroy').bootstrapTable(requisiteTableStructure);

    // Handles when the user clicks to resync courses
    $resyncCoursesBtn.click(function() {
        isSyncing = !isSyncing;
        httpPost({ sync: isSyncing });
        if (isSyncing) {
            $resyncCoursesBtn.html('<i class="fa fa-sync"></i> Abort')
        } else {
            $resyncCoursesBtn.html('<i class="fa fa-sync"></i> Resync')
        }
    });

    // Handles when the user clicks to create a new course
    $createCourseBtn.click(function() {
        resetReqisites();
        $createRequisitesTable.bootstrapTable('load', requisites);
        $createCourseModal.modal('show');
    });

    // Handles when the user clicks to add an created course requisite
    $createCourseRequisiteAdd.click(function() {
        let group = $createCourseRequisiteGroup.val();
        let type = $createCourseRequisiteType.val().toLowerCase();
        let code = $createCourseRequisiteCode.val();
        if (group !== undefined 
            && type !== undefined 
            && code !== undefined) {
                addRequisite(group, type, code);
                $createRequisitesTable.bootstrapTable('load', requisites);
            }
    });

    // Handles when the user clicks to save a newly created course
    $createCourseSave.click(function() {
        httpPost({
            create: {
                code: $createCourseCode.val(),
                name: $createCourseName.val(),
                term: $createCourseTerm.val(),
                credits: $createCourseCredits.val(),
                requisites: exportRequisites(),
            }
        });
    });

    // Handles when the user clicks to edit an existing course
    $editCourseBtn.click(function() {
        let selection = getSelectedRow();
        if (selection) {
            oldTerm = selection.term;
            $editCourseCode.val(selection.code);
            $editCourseName.val(selection.name);
            $editCourseTerm.val(selection.term);
            $editCourseCredits.val(selection.credits);
            initRowRequisites(selection);
            $editRequisitesTable.bootstrapTable('load', requisites);
            $editCourseModal.modal('show');
        }
    });

    // Handles when the user clicks to add an edited course requisite
    $editCourseRequisiteAdd.click(function() {
        let group = $editCourseRequisiteGroup.val();
        let type = $editCourseRequisiteType.val().toLowerCase();
        let code = $editCourseRequisiteCode.val();
        if (group !== undefined 
            && type !== undefined 
            && code !== undefined) {
                addRequisite(group, type, code);
                $editRequisitesTable.bootstrapTable('load', requisites);
            }
    });

    // Handles when the user clicks to save an edited course
    $editCourseSave.click(function() {
        httpPost({
            change: {
                code: $editCourseCode.val(),
                oldterm: oldTerm,
                name: $editCourseName.val(),
                term: $editCourseTerm.val(),
                credits: $editCourseCredits.val(),
                requisites: exportRequisites(),
            }
        });
    });

    // Handles when the user clicks to delete existing courses
    $deleteCoursesBtn.click(function() {
        let row_ids = $.map($coursesTable.bootstrapTable('getSelections'), function(row) {
            return row.id;
        });
        let postback = $.map($coursesTable.bootstrapTable('getSelections'), function(row) {
            return [[row.code, row.term]];
        });

        // directly remove the entries from the table to avoid having to reload it
        $coursesTable.bootstrapTable('remove', {
            field: 'id',
            values: row_ids
        });

        // disable the deletion button since nothing is selected
        $deleteCoursesBtn.prop('disabled', true);

        // send deletion request to webserver
        httpPost({ delete: postback });
    });

});
