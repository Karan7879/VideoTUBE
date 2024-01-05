pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Latitude is correct", function () {
    pm.expect(responseJson.coord.lat).to.equal(51.51);
});

pm.test("Longitude is correct", function () {
    pm.expect(responseJson.coord.lon).to.equal(-0.13);
});

pm.test("Temperature is within expected range", function () {
    pm.expect(responseJson.main.temp).to.be.within(270, 300); 

});

pm.test("Weather description is as expected", function () {
    pm.expect(responseJson.weather[0].description).to.equal("light intensity drizzle");
});

pm.test("Wind speed is within expected range", function () {
    pm.expect(responseJson.wind.speed).to.be.at.least(0);
});


