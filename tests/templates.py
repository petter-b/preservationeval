"""
HTML and JavaScript templates for the test environment.

This module contains the templates needed to create the browser-based
test environment for running the original JavaScript implementation.
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="dp.js"></script>
    <script>
        function runTests(inputs) {
            return inputs.map(input => {
                const t = input[0];
                const rh = input[1];
                return {
                    temp: t,
                    rh: rh,
                    pi: pi(t, rh),
                    emc: emc(t, rh),
                    mold: mold(t, rh)
                };
            });
        }
    </script>
</head>
<body>
</body>
</html>
"""

NODE_SCRIPT_TEMPLATE = """
const puppeteer = require('puppeteer');

async function runTests() {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    await page.goto('file://' + process.argv[2]);

    let data = '';
    process.stdin.resume();
    process.stdin.setEncoding('utf8');

    process.stdin.on('data', (chunk) => {
        data += chunk;
    });

    process.stdin.on('end', async () => {
        const inputs = JSON.parse(data);
        const results = await page.evaluate((testInputs) => {
            return runTests(testInputs);
        }, inputs);
        console.log(JSON.stringify(results));
        await browser.close();
    });
}

runTests().catch(console.error);
"""
