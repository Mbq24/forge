using Microsoft.AspNetCore.Mvc;
using RegressionModelLong.Model;

namespace RegressionModelLong.ConsoleApp.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class ModelController : ControllerBase
    {
        [HttpPost("predict")]
        public IActionResult Predict([FromBody] ModelInput input)
        {
            ModelOutput result = ConsumeModel.Predict(input);
            return Ok(result);
        }
    }
}