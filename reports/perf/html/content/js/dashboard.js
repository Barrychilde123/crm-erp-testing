/*
   Licensed to the Apache Software Foundation (ASF) under one or more
   contributor license agreements.  See the NOTICE file distributed with
   this work for additional information regarding copyright ownership.
   The ASF licenses this file to You under the Apache License, Version 2.0
   (the "License"); you may not use this file except in compliance with
   the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/
var showControllersOnly = false;
var seriesFilter = "";
var filtersOnlySampleSeries = true;

/*
 * Add header in statistics table to group metrics by category
 * format
 *
 */
function summaryTableHeader(header) {
    var newRow = header.insertRow(-1);
    newRow.className = "tablesorter-no-sort";
    var cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Requests";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 3;
    cell.innerHTML = "Executions";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 7;
    cell.innerHTML = "Response Times (ms)";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Throughput";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 2;
    cell.innerHTML = "Network (KB/sec)";
    newRow.appendChild(cell);
}

/*
 * Populates the table identified by id parameter with the specified data and
 * format
 *
 */
function createTable(table, info, formatter, defaultSorts, seriesIndex, headerCreator) {
    var tableRef = table[0];

    // Create header and populate it with data.titles array
    var header = tableRef.createTHead();

    // Call callback is available
    if(headerCreator) {
        headerCreator(header);
    }

    var newRow = header.insertRow(-1);
    for (var index = 0; index < info.titles.length; index++) {
        var cell = document.createElement('th');
        cell.innerHTML = info.titles[index];
        newRow.appendChild(cell);
    }

    var tBody;

    // Create overall body if defined
    if(info.overall){
        tBody = document.createElement('tbody');
        tBody.className = "tablesorter-no-sort";
        tableRef.appendChild(tBody);
        var newRow = tBody.insertRow(-1);
        var data = info.overall.data;
        for(var index=0;index < data.length; index++){
            var cell = newRow.insertCell(-1);
            cell.innerHTML = formatter ? formatter(index, data[index]): data[index];
        }
    }

    // Create regular body
    tBody = document.createElement('tbody');
    tableRef.appendChild(tBody);

    var regexp;
    if(seriesFilter) {
        regexp = new RegExp(seriesFilter, 'i');
    }
    // Populate body with data.items array
    for(var index=0; index < info.items.length; index++){
        var item = info.items[index];
        if((!regexp || filtersOnlySampleSeries && !info.supportsControllersDiscrimination || regexp.test(item.data[seriesIndex]))
                &&
                (!showControllersOnly || !info.supportsControllersDiscrimination || item.isController)){
            if(item.data.length > 0) {
                var newRow = tBody.insertRow(-1);
                for(var col=0; col < item.data.length; col++){
                    var cell = newRow.insertCell(-1);
                    cell.innerHTML = formatter ? formatter(col, item.data[col]) : item.data[col];
                }
            }
        }
    }

    // Add support of columns sort
    table.tablesorter({sortList : defaultSorts});
}

$(document).ready(function() {

    // Customize table sorter default options
    $.extend( $.tablesorter.defaults, {
        theme: 'blue',
        cssInfoBlock: "tablesorter-no-sort",
        widthFixed: true,
        widgets: ['zebra']
    });

    var data = {"OkPercent": 100.0, "KoPercent": 0.0};
    var dataset = [
        {
            "label" : "FAIL",
            "data" : data.KoPercent,
            "color" : "#FF6347"
        },
        {
            "label" : "PASS",
            "data" : data.OkPercent,
            "color" : "#9ACD32"
        }];
    $.plot($("#flot-requests-summary"), dataset, {
        series : {
            pie : {
                show : true,
                radius : 1,
                label : {
                    show : true,
                    radius : 3 / 4,
                    formatter : function(label, series) {
                        return '<div style="font-size:8pt;text-align:center;padding:2px;color:white;">'
                            + label
                            + '<br/>'
                            + Math.round10(series.percent, -2)
                            + '%</div>';
                    },
                    background : {
                        opacity : 0.5,
                        color : '#000'
                    }
                }
            }
        },
        legend : {
            show : true
        }
    });

    // Creates APDEX table
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [1.0, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [1.0, 500, 1500, "POST /api/customers (write)"], "isController": false}, {"data": [1.0, 500, 1500, "GET /api/customers?q=蓝海"], "isController": false}, {"data": [1.0, 500, 1500, "GET /api/customers?q=物流"], "isController": false}, {"data": [1.0, 500, 1500, "GET /api/customers?q=科技"], "isController": false}, {"data": [1.0, 500, 1500, "POST /api/login"], "isController": false}, {"data": [1.0, 500, 1500, "GET /api/customers?q=能源"], "isController": false}, {"data": [1.0, 500, 1500, "GET /api/customers?q=医疗"], "isController": false}, {"data": [1.0, 500, 1500, "GET /api/customers?q=启明"], "isController": false}, {"data": [1.0, 500, 1500, "GET /api/customers?q=智能"], "isController": false}, {"data": [1.0, 500, 1500, "GET /api/customers?q=星河"], "isController": false}, {"data": [1.0, 500, 1500, "GET /api/customers?q=恒远"], "isController": false}, {"data": [1.0, 500, 1500, "GET /api/customers?q=制造"], "isController": false}]}, function(index, item){
        switch(index){
            case 0:
                item = item.toFixed(3);
                break;
            case 1:
            case 2:
                item = formatDuration(item);
                break;
        }
        return item;
    }, [[0, 0]], 3);

    // Create statistics table
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 600, 0, 0.0, 53.3516666666667, 3, 227, 7.0, 153.0, 158.0, 175.98000000000002, 55.25370660281794, 21.69733199419836, 17.142678308315684], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["POST /api/customers (write)", 200, 0, 0.0, 7.5799999999999965, 3, 227, 5.0, 10.0, 15.0, 29.910000000000082, 18.73536299765808, 4.786848653395785, 6.714724824355971], "isController": false}, {"data": ["GET /api/customers?q=蓝海", 20, 0, 0.0, 5.050000000000001, 3, 11, 4.0, 7.900000000000002, 10.849999999999998, 11.0, 2.090082558261051, 1.0144248354059984, 0.5776302382694116], "isController": false}, {"data": ["GET /api/customers?q=物流", 20, 0, 0.0, 4.3500000000000005, 3, 7, 4.0, 5.900000000000002, 6.949999999999999, 7.0, 2.09183139838929, 1.0152736376948017, 0.5781135602970401], "isController": false}, {"data": ["GET /api/customers?q=科技", 20, 0, 0.0, 5.1, 3, 11, 4.0, 8.700000000000006, 10.899999999999999, 11.0, 2.0815986677768525, 1.0367337114904245, 0.5752855693172356], "isController": false}, {"data": ["POST /api/login", 200, 0, 0.0, 147.27500000000006, 121, 195, 147.0, 161.9, 168.0, 191.94000000000005, 18.43487879067195, 8.91139160291271, 5.4566521107936214], "isController": false}, {"data": ["GET /api/customers?q=能源", 20, 0, 0.0, 5.4, 3, 10, 5.0, 9.700000000000006, 10.0, 10.0, 2.0418580908626853, 0.9810490045941808, 0.5643025778458397], "isController": false}, {"data": ["GET /api/customers?q=医疗", 20, 0, 0.0, 4.75, 3, 11, 4.0, 7.0, 10.799999999999997, 11.0, 2.056978298878947, 0.9742524169495012, 0.5684813072097089], "isController": false}, {"data": ["GET /api/customers?q=启明", 20, 0, 0.0, 5.9, 3, 11, 6.0, 8.900000000000002, 10.899999999999999, 11.0, 2.0298386278290876, 0.4658321069724957, 0.5609807926519842], "isController": false}, {"data": ["GET /api/customers?q=智能", 20, 0, 0.0, 4.450000000000002, 3, 7, 4.0, 6.900000000000002, 7.0, 7.0, 2.082032063293775, 0.47781009265042684, 0.5754053456173225], "isController": false}, {"data": ["GET /api/customers?q=星河", 20, 0, 0.0, 4.15, 3, 8, 4.0, 6.800000000000004, 7.949999999999999, 8.0, 2.0807324178110695, 1.0363022784019975, 0.5750461662505202], "isController": false}, {"data": ["GET /api/customers?q=恒远", 20, 0, 0.0, 7.249999999999999, 4, 18, 6.0, 13.700000000000006, 17.799999999999997, 18.0, 2.0883366398663465, 1.0564046674323901, 0.5771477237130626], "isController": false}, {"data": ["GET /api/customers?q=制造", 20, 0, 0.0, 5.6, 3, 13, 5.0, 8.900000000000002, 12.799999999999997, 13.0, 2.0833333333333335, 1.0538736979166667, 0.5757649739583334], "isController": false}]}, function(index, item){
        switch(index){
            // Errors pct
            case 3:
                item = item.toFixed(2) + '%';
                break;
            // Mean
            case 4:
            // Mean
            case 7:
            // Median
            case 8:
            // Percentile 1
            case 9:
            // Percentile 2
            case 10:
            // Percentile 3
            case 11:
            // Throughput
            case 12:
            // Kbytes/s
            case 13:
            // Sent Kbytes/s
                item = item.toFixed(2);
                break;
        }
        return item;
    }, [[0, 0]], 0, summaryTableHeader);

    // Create error table
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": []}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 600, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
