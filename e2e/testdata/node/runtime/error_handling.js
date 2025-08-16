try {
    const result = JSON.parse('invalid json');
} catch (error) {
    console.log('Caught error:', error.message);
    console.log('Error handled successfully');
}