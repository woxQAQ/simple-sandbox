async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
    console.log("Starting async operation...");
    await delay(1000);
    console.log("Async operation completed!");
}

main().catch(console.error);