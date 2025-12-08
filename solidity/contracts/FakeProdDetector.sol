// solidity/contracts/FakeProdDetector.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

contract FakeProdDetector {
    struct Product {
        string name;
        string color;
        string material;
        uint256 price;
        uint256 year;
    }

    mapping(bytes32 => Product) private products;

    event ProductUploaded(bytes32 indexed id, string name, string color, string material, uint256 price, uint256 year);

    function uploadProduct(
        bytes32 id,
        string memory name,
        string memory color,
        string memory material,
        uint256 price,
        uint256 year
    ) public {
        products[id] = Product(name, color, material, price, year);
        emit ProductUploaded(id, name, color, material, price, year);
    }

    function getProduct(bytes32 id) public view returns (
        string memory name,
        string memory color,
        string memory material,
        uint256 price,
        uint256 year
    ) {
        Product memory p = products[id];
        return (p.name, p.color, p.material, p.price, p.year);
    }
}
