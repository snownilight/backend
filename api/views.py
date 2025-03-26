from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import F
from .models import Category, Product, Warehouse, Inventory, StockMovement
from .serializers import (
    CategorySerializer, ProductSerializer, WarehouseSerializer,
    InventorySerializer, StockMovementSerializer
)

# Create your views here.

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['category', 'sku']
    search_fields = ['name', 'sku', 'description']

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['manager']
    search_fields = ['name', 'location']

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['warehouse', 'product']
    search_fields = ['product__name', 'warehouse__name']

    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        inventory = self.get_object()
        quantity = request.data.get('quantity')
        movement_type = request.data.get('movement_type')
        notes = request.data.get('notes', '')

        if not quantity or not movement_type:
            return Response(
                {'error': 'Quantity and movement_type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create stock movement
        movement = StockMovement.objects.create(
            product=inventory.product,
            warehouse=inventory.warehouse,
            movement_type=movement_type,
            quantity=quantity,
            notes=notes,
            created_by=request.user,
            reference_number=f"MOV-{StockMovement.objects.count() + 1}"
        )

        # Update inventory
        if movement_type == 'IN':
            inventory.quantity = F('quantity') + quantity
        else:
            if inventory.quantity < quantity:
                return Response(
                    {'error': 'Insufficient stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            inventory.quantity = F('quantity') - quantity
        
        inventory.save()
        inventory.refresh_from_db()

        return Response({
            'inventory': InventorySerializer(inventory).data,
            'movement': StockMovementSerializer(movement).data
        })

class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['warehouse', 'product', 'movement_type']
    search_fields = ['product__name', 'warehouse__name', 'reference_number']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
