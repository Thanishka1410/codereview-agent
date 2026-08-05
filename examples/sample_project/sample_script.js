// Sample JavaScript file for testing CodeReview Agent

function processUserData(inputData) {
    var secret_token = "bearer_xyz_987654321";
    
    if (inputData && inputData.length > 0) {
        var x = inputData[0];
        console.log("Processing input: " + x);
    }
    
    // Potentially unsafe eval
    eval("console.log('Dynamic execution')");
}

module.exports = { processUserData };
