// ---------------- PIE CHART ----------------
// the canvas element with the id 'expenseChart' from the HTML document and assigns it to the variable pieCtx
const pieCtx = document.getElementById('expenseChart');

new Chart(pieCtx, {

    type: 'pie',

    data: {

        labels: pieLabels,

        datasets: [{

            label: 'Expenses', // labels such as food entertainment, etc.

            data: pieValues, // the corresponding values for each label

            borderWidth: 2

        }]

    },
    // options controlls the appearence of the piechart
    options: {
        //if screen size changes, the chart will adjust its size accordingly
        responsive: true,
        // plugins provide some extra functionalities to the chart, such as legends and titles
        plugins: {
            // legend is the box that shows what each color in the pie chart represents
            legend: {

                position: 'bottom'

            },

            title: {

                display: true,

                text: 'Category Wise Spending'

            }

        }

    }

});

// ---------------- LINE CHART ----------------

const lineCtx = document.getElementById('lineChart');

new Chart(lineCtx, {

    type: 'line',

    data: {
        // X axis labels for the line chart, which are the dates of the expenses
        labels: lineLabels,

        datasets: [{

            label: 'Daily Spending',
            // Y axis values for the line chart, which are the total expenses for each date
            data: lineValues,

            borderWidth: 3,
            // fill: false means that the area under the line will not be filled with color if true are under is colored
            fill: false,
            // controlls the curve of the line.
            // 0 is a straight line, 1 is a very curvy line
            tension: 0.3

        }]

    },

    options: {

        responsive: true,

        plugins: {

            legend: {

                position: 'bottom'

            },

            title: {

                display: true,

                text: 'Daily Expense Trend'

            }

        },

        scales: {

            y: {

                beginAtZero: true

            }

        }

    }

});