const promise1 = Promise.resolve('First promise');
const promise2 = Promise.resolve('Second promise');

Promise.all([promise1, promise2])
    .then(results => {
        console.log('All promises resolved:');
        results.forEach((result, index) => {
            console.log('Promise ' + (index + 1) + ': ' + result);
        });
    })
    .catch(error => {
        console.error('Promise error:', error);
    });